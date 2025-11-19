import click
from rich.console import Console

from .. import lib

console = Console()


@click.command("build")
@click.argument("challenges", nargs=-1, required=True)
def build_command(challenges):
    """Render and build one or more challenges."""
    for path_argument in challenges:
        try:
            challenge_path = lib.resolve_path(path_argument)
        except FileNotFoundError as error:
            raise click.ClickException(str(error)) from error
        if not challenge_path.is_dir():
            raise click.ClickException(f"build expects a challenge directory, got: {challenge_path}")
        try:
            image_id = lib.build_challenge(challenge_path)
        except RuntimeError as error:
            raise click.ClickException(str(error)) from error
        console.print(f"[green]Built[/] {image_id}")
