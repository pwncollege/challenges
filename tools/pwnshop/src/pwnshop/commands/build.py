import logging
import pathlib

import click

from .. import lib
from ..console import console

logger = logging.getLogger(__name__)


@click.command("build")
@click.option("--modified-since", metavar="REF", help="Only include challenges changed versus REF.")
@click.argument(
    "targets",
    nargs=-1,
    required=True,
    type=click.Path(path_type=pathlib.Path, exists=True, dir_okay=True, file_okay=False, resolve_path=False),
)
def build_command(targets, modified_since):
    """Build one or more challenges."""
    if not (challenge_paths := lib.resolve_targets(targets, modified_since=modified_since)):
        if modified_since:
            console.print(f"[yellow]No challenges found since {modified_since}[/]")
            return
        raise click.ClickException("No challenges found in provided targets.")
    logger.info("building %d challenge(s)", len(challenge_paths))
    for challenge_path in challenge_paths:
        try:
            image_id = lib.build_challenge(challenge_path)
        except RuntimeError as error:
            raise click.ClickException(str(error)) from error
        click.echo(image_id)
