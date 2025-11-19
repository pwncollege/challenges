import subprocess

import click
from rich.console import Console

from .. import lib

console = Console()


@click.command("test")
@click.argument("challenges", nargs=-1, required=True)
def test_command(challenges):
    """Build and run tests for one or more challenges."""
    failed = {}
    for path_argument in challenges:
        try:
            challenge_path = lib.resolve_path(path_argument)
        except FileNotFoundError as error:
            raise click.ClickException(str(error)) from error
        if not challenge_path.is_dir():
            raise click.ClickException(f"test expects a challenge directory, got: {challenge_path}")
        try:
            rendered_directory = lib.render_challenge(challenge_path)
        except FileNotFoundError as error:
            raise click.ClickException(str(error)) from error
        try:
            image_id = lib.build_challenge(challenge_path)
        except RuntimeError as error:
            raise click.ClickException(str(error)) from error
        tests = sorted(rendered_directory.rglob("test*/test_*"))
        if not tests:
            console.print(f"[yellow]No tests found[/] for {path_argument}")
            continue
        for test_file in tests:
            with lib.run_challenge(image_id, volumes=[test_file]) as (container, flag):
                result = subprocess.run(["docker", "exec", "--user=1000:1000", container, f"{test_file}"])
                relative_path = test_file.relative_to(rendered_directory)
                if result.returncode != 0:
                    failed.setdefault(path_argument, []).append(relative_path)
                    console.print(f"[red]FAIL[/] {path_argument}/{relative_path}")
                else:
                    console.print(f"[green]PASS[/] {path_argument}/{relative_path}")
    if failed:
        console.print("[red]The following tests have failed:[/]")
        for challenge_name, test_list in failed.items():
            for test_path in test_list:
                console.print(f"- {challenge_name}/{test_path}")
        raise click.ClickException("Some tests have failed.")
