import pathlib

import click
from rich.console import Console

from .. import lib

console = Console()


@click.command("list")
@click.option("--modified-since", metavar="REF", help="Only include challenges changed versus REF.")
@click.argument(
    "targets",
    nargs=-1,
    type=click.Path(exists=True, file_okay=False, resolve_path=False, path_type=pathlib.Path),
)
def list_command(modified_since, targets):
    """List challenges."""
    root_targets = targets or (pathlib.Path("."),)
    challenges = {
        challenge for target in root_targets for challenge in lib.list_challenges(target, modified_since=modified_since)
    }
    for challenge in sorted(challenges):
        console.print(str(challenge), highlight=False)
