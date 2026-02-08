import logging
import pathlib
import subprocess

import click

from .. import lib

logger = logging.getLogger(__name__)


def resolve_nix_packages(packages: list[str]) -> list[pathlib.Path]:
    """Resolve nix package names to store paths using nix build."""
    if not packages:
        return []
    paths = []
    for pkg in packages:
        logger.debug("resolving nix package: %s", pkg)
        try:
            result = subprocess.run(
                [
                    "nix",
                    "--extra-experimental-features", "nix-command flakes",
                    "build",
                    f"nixpkgs#{pkg}",
                    "--print-out-paths",
                    "--no-link",
                ],
                text=True,
                capture_output=True,
                check=True,
            )
            for line in result.stdout.strip().splitlines():
                if line:
                    paths.append(pathlib.Path(line))
                    logger.debug("resolved %s -> %s", pkg, line)
        except subprocess.CalledProcessError as e:
            stderr = e.stderr.strip() if e.stderr else "unknown error"
            raise click.ClickException(f"Failed to resolve nix package '{pkg}': {stderr}") from e
        except FileNotFoundError:
            raise click.ClickException("nix command not found. Is Nix installed?")
    return paths


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
    "--nix-packages",
    "nix_packages",
    default="",
    help="Comma-separated list of Nix packages to make available in the container (e.g., gdb,python3).",
)
@click.argument("command", nargs=-1, default=("/bin/bash",))
def run_command(challenge_path, user, volumes, nix_packages, command):
    """Run interactive shell for a challenge."""
    try:
        image_id = lib.build_challenge(challenge_path)
    except RuntimeError as error:
        raise click.ClickException(str(error)) from error
    resolved_volumes = [path.resolve() for path in volumes]

    # Resolve nix packages to store paths
    nix_paths = []
    if nix_packages:
        pkg_list = [p.strip() for p in nix_packages.split(",") if p.strip()]
        nix_paths = resolve_nix_packages(pkg_list)

    logger.info("running %s as uid=%d, command=%s", challenge_path, user, list(command))
    with lib.run_challenge(image_id, volumes=resolved_volumes, nix_paths=nix_paths) as (container, flag):
        subprocess.run(["docker", "exec", f"--user={user}", "-it", container, *command])
