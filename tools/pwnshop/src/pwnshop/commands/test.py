import logging
import multiprocessing
import multiprocessing.pool
import os
import pathlib
import shutil
import subprocess
import click
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)
from .. import lib
from ..console import console

logger = logging.getLogger(__name__)


@click.command("test")
@click.option("--modified-since", metavar="REF", help="Only include challenges changed versus REF.")
@click.option("--jobs", "-j", metavar="N", type=click.IntRange(1, None), help="Parallel challenges (default: cores).")
@click.option("--require-tests", is_flag=True, help="Fail if any challenge has no tests.")
@click.option(
    "--test-timeout",
    metavar="N",
    type=click.IntRange(1, None),
    default=None,
    help="Timeout in seconds for each individual test.",
)
@click.option(
    "--log-failures",
    metavar="DIR",
    type=click.Path(path_type=pathlib.Path, file_okay=False, resolve_path=True),
    help="Write failure output to DIR/challenge/test.log files.",
)
@click.argument(
    "targets",
    nargs=-1,
    required=True,
    type=click.Path(
        path_type=pathlib.Path,
        exists=True,
        dir_okay=True,
        file_okay=False,
        resolve_path=False,
    ),
)
def test_command(targets, modified_since, jobs, require_tests, test_timeout, log_failures):
    """Test one or more challenges."""
    if not (challenge_paths := lib.resolve_targets(targets, modified_since=modified_since)):
        if modified_since:
            console.print(f"[yellow]No challenges found since {modified_since}[/]")
            return
        raise click.ClickException("No challenges found in provided targets.")
    jobs = jobs or os.cpu_count() or 1
    failed: dict[pathlib.Path, list] = {}
    passed_count = failed_count = total_tests = failed_tests = 0

    def test_challenge(challenge_path):
        challenge_path = pathlib.Path(challenge_path)
        rendered = None
        try:
            config = lib.load_challenge_config(challenge_path)
            rendered = lib.render_challenge(challenge_path)
            image_id = lib.build_challenge(challenge_path)
            tests = sorted(rendered.rglob("test*/test_*"))
            if not tests:
                logger.warning("no tests found for %s", challenge_path)
                return {"path": challenge_path, "tests": []}
            logger.info("running %d test(s) for %s", len(tests), challenge_path)
            results = []
            for test in tests:
                test_name = test.relative_to(rendered)
                logger.debug("running test %s in %s", test_name, challenge_path)
                with lib.run_challenge(image_id, volumes=[test], privileged=config["privileged"]) as (container, _):
                    try:
                        run = subprocess.run(
                            ["docker", "exec", "--user=1000:1000", container, f"{test}"],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT,
                            text=True,
                            timeout=test_timeout,
                        )
                    except subprocess.TimeoutExpired as e:
                        logger.warning("test %s timed out after %ds in %s", test_name, test_timeout, challenge_path)
                        results.append((test_name, False, f"TIMEOUT after {test_timeout}s\n{e.stdout or ''}"))
                        continue
                passed = run.returncode == 0
                logger.debug("test %s %s (rc=%d)", test_name, "PASSED" if passed else "FAILED", run.returncode)
                results.append((test_name, passed, run.stdout or ""))
            return {"path": challenge_path, "tests": results}
        except (FileNotFoundError, RuntimeError, subprocess.CalledProcessError) as error:
            logger.error("test setup failed for %s: %s", challenge_path, error)
            return {"path": challenge_path, "error": str(error)}
        finally:
            if rendered:
                shutil.rmtree(rendered, ignore_errors=True)

    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        MofNCompleteColumn(),
        TimeElapsedColumn(),
        TimeRemainingColumn(),
        console=console,
        transient=True,
    ) as progress:
        task = progress.add_task("Testing challenges", total=len(challenge_paths))
        pool = multiprocessing.pool.ThreadPool(processes=jobs)
        completed = 0
        for result in pool.imap_unordered(test_challenge, challenge_paths):
            challenge = result["path"]
            error = result.get("error")
            tests = result.get("tests") or []
            if error:
                failed.setdefault(challenge, []).append("<build>")
                failed_count += 1
                if log_failures:
                    log_file = log_failures / challenge / "_build_error.log"
                    log_file.parent.mkdir(parents=True, exist_ok=True)
                    log_file.write_text(error)
                else:
                    console.print(f"[red]FAIL[/] {challenge}: {error}")
            elif not tests:
                if require_tests:
                    console.print(f"[red]FAIL[/] {challenge}: no tests found")
                    failed.setdefault(challenge, []).append("<no tests>")
                    failed_count += 1
                else:
                    passed_count += 1
            else:
                for test_path, passed, output in tests:
                    total_tests += 1
                    if passed:
                        continue
                    failed_tests += 1
                    failed.setdefault(challenge, []).append(test_path)
                    if output:
                        if log_failures:
                            log_file = log_failures / challenge / f"{test_path}.log"
                            log_file.parent.mkdir(parents=True, exist_ok=True)
                            log_file.write_text(output)
                        else:
                            console.print(output.rstrip("\n"), markup=False)
                if challenge in failed:
                    failed_count += 1
                else:
                    passed_count += 1
            completed += 1
            progress.update(
                task,
                advance=1,
                description=f"Testing challenges (pass: {passed_count}, fail: {failed_count})",
            )
            if not console.is_terminal:
                console.print(
                    f"Testing challenges (pass: {passed_count}, fail: {failed_count}) "
                    f"[{completed}/{len(challenge_paths)}]"
                )
        pool.close()
        pool.join()

    if failed:
        console.print("[red]Some tests failed:[/]")
        for challenge_path, test_list in failed.items():
            for test_path in test_list:
                console.print(f"- {challenge_path}/{test_path}")
        console.print(f"Ran {total_tests} testcases across {len(challenge_paths)} challenges (failed: {failed_tests})")
        raise click.ClickException("Some tests have failed.")
    console.print(f"[green]All tests passed ({passed_count} challenges, {total_tests} testcases)[/]")
