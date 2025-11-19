import json

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
def list_command(modified_since, output_format):
    """List challenges grouped by git-crypt key."""
    group_challenges = lib.discover_challenges(modified_since=modified_since)
    if output_format == "matrix":
        matrix = {
            "group": list(group_challenges.keys()),
            "include": [
                {"group": group, "challenges": "\n".join(challenges)}
                for group, challenges in group_challenges.items()
            ],
        }
        click.echo(json.dumps(matrix, separators=(",", ":")))
        return
    rows = [
        (group, challenge)
        for group, challenges in group_challenges.items()
        for challenge in challenges
    ]
    group_width = max(len("GROUP"), *(len(group) for group, _ in rows)) if rows else len("GROUP")
    path_width = max(len("PATH"), *(len(path) for _, path in rows)) if rows else len("PATH")
    fmt = f"{{:<{group_width}}}  {{:<{path_width}}}"
    console.print(fmt.format("GROUP", "PATH"), highlight=False)
    for group, challenge in rows:
        console.print(fmt.format(group, challenge), highlight=False)
