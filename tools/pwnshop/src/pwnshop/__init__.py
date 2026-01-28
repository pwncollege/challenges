import logging

import click

from .commands.build import build_command
from .commands.list import list_command
from .commands.render import render_command
from .commands.run import run_command
from .commands.test import test_command

VERBOSITY_LEVELS = [logging.ERROR, logging.WARNING, logging.INFO, logging.DEBUG]


@click.group()
@click.option("-v", "--verbose", count=True, help="Increase verbosity (repeat for more: -v, -vv, -vvv).")
def cli(verbose):
    """Challenge management CLI."""
    level = VERBOSITY_LEVELS[min(verbose, len(VERBOSITY_LEVELS) - 1)]
    logging.basicConfig(format="%(levelname)s: %(message)s", level=level)


cli.add_command(render_command)
cli.add_command(build_command)
cli.add_command(test_command)
cli.add_command(run_command)
cli.add_command(list_command)
