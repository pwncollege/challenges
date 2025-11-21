import json
import pathlib

import click
from rich.console import Console

from .. import lib

console = Console()


@click.command("list")
@click.option("--modified-since", metavar="REF", help="Only include challenges changed versus REF.")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["table", "matrix"]),
    default="table",
    show_default=True,
)
@click.argument(
    "directory",
    required=False,
    type=click.Path(exists=True, file_okay=False, resolve_path=True, path_type=pathlib.Path),
)
def list_command(modified_since, output_format, directory):
    """List challenges by group."""
    root_directory = directory or pathlib.Path.cwd()
    groups = [pathlib.Path(group) for group in lib.list_groups(root_directory)]
    group_challenges = {}
    for challenge in lib.list_challenges(root_directory, modified_since=modified_since):
        challenge_path = pathlib.Path(challenge)
        group_name = "default"
        challenge_name = challenge_path.as_posix()
        for group in groups:
            if challenge_path.is_relative_to(group):
                group_name = group.as_posix()
                challenge_name = challenge_path.relative_to(group).as_posix()
                break
        group_challenges.setdefault(group_name, []).append(challenge_name)
    for group in group_challenges:
        group_challenges[group].sort()
    ordered_groups = sorted(group_challenges)
    if output_format == "matrix":
        matrix = {
            "group": ordered_groups,
            "include": [
                {"group": group, "challenges": "\n".join(group_challenges[group])} for group in ordered_groups
            ],
        }
        click.echo(json.dumps(matrix, separators=(",", ":")))
        return
    rows = [(group, challenge) for group in ordered_groups for challenge in group_challenges[group]]
    group_width = max(len("GROUP"), *(len(group) for group, _ in rows)) if rows else len("GROUP")
    path_width = max(len("PATH"), *(len(path) for _, path in rows)) if rows else len("PATH")
    fmt = f"{{:<{group_width}}}  {{:<{path_width}}}"
    console.print(fmt.format("GROUP", "PATH"), highlight=False)
    for group, challenge in rows:
        console.print(fmt.format(group, challenge), highlight=False)
