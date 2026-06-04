import logging
import pathlib
import shlex
import shutil
import subprocess

import click

from .. import lib

logger = logging.getLogger(__name__)


@click.command("run", context_settings=dict(allow_interspersed_args=False))
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
@click.option(
    "--cast-to",
    "cast_to",
    type=click.Path(path_type=pathlib.Path, dir_okay=False, writable=True),
    default=None,
    help="Record the session to an asciinema v2 .cast file (replay with `asciinema play`).",
)
@click.argument("command", nargs=-1, default=("/bin/bash",))
def run_command(challenge_path, user, volumes, cast_to, command):
    """Run interactive shell for a challenge."""
    try:
        image_id = lib.build_challenge(challenge_path)
    except RuntimeError as error:
        raise click.ClickException(str(error)) from error
    resolved_volumes = [path.resolve() for path in volumes]
    logger.info("running %s as uid=%d, command=%s", challenge_path, user, list(command))
    with lib.run_challenge(challenge_path, image_id, volumes=resolved_volumes) as (container, flag):
        docker_command = ["docker", "exec", f"--user={user}", "-it", container, *command]
        if cast_to is None:
            subprocess.run(docker_command)
        else:
            if not shutil.which("asciinema"):
                raise click.ClickException(
                    "--cast-to requires `asciinema` on PATH (it's in the nix dev shell)."
                )
            cols, rows = shutil.get_terminal_size((100, 30))
            logger.info("recording session to %s", cast_to)
            subprocess.run(
                [
                    "asciinema", "rec",
                    "--command", shlex.join(docker_command),
                    "--overwrite", "--quiet",
                    "--cols", str(cols), "--rows", str(rows),
                    "--title", f"{challenge_path.name} (pwnshop run)",
                    str(cast_to),
                ],
                check=True,
            )
            click.echo(f"Session recorded to {cast_to}", err=True)
