import logging
import pathlib
import subprocess

import click

from .. import lib

logger = logging.getLogger(__name__)


@click.command("run")
@click.argument(
    "challenge_path",
    type=click.Path(path_type=pathlib.Path, exists=True, dir_okay=True, file_okay=False, resolve_path=True),
)
@click.option(
    "--user",
    "user",
    type=int,
    default=1000,
    show_default=True,
    help="User to interactively run as.",
)
@click.option(
    "--volume",
    "volumes",
    type=click.Path(path_type=pathlib.Path, exists=True, dir_okay=True, file_okay=True),
    multiple=True,
    help="Host path to mount read-only at the same location inside the container (repeatable).",
)
@click.argument("command", nargs=-1, default=("/bin/bash",))
def run_command(challenge_path, user, volumes, command):
    """Run interactive shell for a challenge."""
    try:
        image_id = lib.build_challenge(challenge_path)
    except RuntimeError as error:
        raise click.ClickException(str(error)) from error
    resolved_volumes = [path.resolve() for path in volumes]
    logger.info("running %s as uid=%d, command=%s", challenge_path, user, list(command))
    with lib.run_challenge(image_id, volumes=resolved_volumes) as (container, flag):
        subprocess.run(["docker", "exec", f"--user={user}", "-it", container, *command])
