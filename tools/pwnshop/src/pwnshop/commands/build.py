import pathlib

import click
from rich.console import Console

from .. import lib

console = Console()


@click.command("build")
@click.argument(
    "challenges",
    nargs=-1,
    required=True,
    type=click.Path(path_type=pathlib.Path, exists=True, dir_okay=True, file_okay=False, resolve_path=True),
)
def build_command(challenges):
    """Render and build one or more challenges."""
    for challenge_path in challenges:
        try:
            image_id = lib.build_challenge(challenge_path)
        except RuntimeError as error:
            raise click.ClickException(str(error)) from error
        console.print(f"[green]Built[/] {image_id}")
