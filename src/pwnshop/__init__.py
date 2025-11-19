import click

from .commands.build import build_command
from .commands.list import list_command
from .commands.render import render_command
from .commands.run import run_command
from .commands.test import test_command


@click.group()
def cli():
    """Challenge builder utility."""


cli.add_command(render_command)
cli.add_command(build_command)
cli.add_command(test_command)
cli.add_command(run_command)
cli.add_command(list_command)


__all__ = ["cli"]
