import pathlib
import subprocess

import click

from .. import lib


@click.command("run")
@click.argument("challenge_path", type=str)
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
    """Drop into an interactive shell inside a challenge container."""
    try:
        resolved_path = lib.resolve_path(challenge_path)
    except FileNotFoundError as error:
        raise click.ClickException(str(error)) from error
    if not resolved_path.is_dir():
        raise click.ClickException(f"run expects a challenge directory, got: {resolved_path}")
    try:
        image_id = lib.build_challenge(resolved_path)
    except RuntimeError as error:
        raise click.ClickException(str(error)) from error
    resolved_volumes = [path.resolve().as_posix() for path in volumes]
    with lib.run_challenge(image_id, volumes=resolved_volumes) as (container, flag):
        subprocess.run(["docker", "exec", f"--user={user}", "-it", container, *command])
