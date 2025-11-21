import pathlib
import subprocess

import click
from rich.console import Console

from .. import lib

console = Console()


@click.command("test")
@click.argument(
    "targets",
    nargs=-1,
    required=True,
    type=click.Path(path_type=pathlib.Path, exists=True, dir_okay=True, file_okay=False, resolve_path=False),
)
def test_command(targets):
    """Test one or more challenges."""
    if not (challenge_paths := lib.resolve_targets(targets)):
        raise click.ClickException("No challenges found in provided targets.")
    failed = {}
    for challenge_path in challenge_paths:
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
            console.print(f"[yellow]No tests found[/] for {challenge_path}")
            continue
        for test_file in tests:
            with lib.run_challenge(image_id, volumes=[test_file]) as (container, flag):
                result = subprocess.run(["docker", "exec", "--user=1000:1000", container, f"{test_file}"])
                relative_path = test_file.relative_to(rendered_directory)
                if result.returncode != 0:
                    failed.setdefault(challenge_path, []).append(relative_path)
                    console.print(f"[red]FAIL[/] {challenge_path}/{relative_path}")
                else:
                    console.print(f"[green]PASS[/] {challenge_path}/{relative_path}")
    if failed:
        console.print("[red]The following tests have failed:[/]")
        for challenge_path, test_list in failed.items():
            for test_path in test_list:
                console.print(f"- {challenge_path}/{test_path}")
        raise click.ClickException("Some tests have failed.")
