#!/bin/env python3

import tempfile
import argparse
import pyastyle
import logging
import pathlib
import random
import shutil
import jinja2
import black
import sys
import os
import re

LOG = logging.getLogger(__name__)

def render(template):
    class MockChallenge:
        random = random.Random(1338)

    env = jinja2.Environment(loader=jinja2.FileSystemLoader(list(pathlib.Path(template).parents)))
    jinja_template = env.get_template(os.path.basename(template))
    rendered = jinja_template.render(challenge=MockChallenge)
    if template.endswith(".py.j2") or "python" in rendered.splitlines()[0]:
        try:
            return black.format_file_contents(rendered, fast=False, mode=black.FileMode(line_length=120))
        except black.parsing.InvalidInput:
            LOG.warning(f"Python template {template} does not format properly.")
            return rendered
        except black.report.NothingChanged:
            return rendered
    elif template.endswith(".c.j2"):
        return re.sub("\n{2,}", "\n\n", pyastyle.format(rendered, "--style=allman"))
    else:
        return rendered

def render_challenge(template_dir, output_dir=None):
    rendered_dir = output_dir or tempfile.mktemp(prefix="chal-")
    shutil.copytree(template_dir, rendered_dir, ignore=shutil.ignore_patterns('TESTS_PRIVATE', 'TESTS_PUBLIC'))

    template_path = pathlib.Path(template_dir)
    rendered_path = pathlib.Path(rendered_dir)

    for j2_file in rendered_path.rglob("*.j2"):
        original_j2_file = template_path / j2_file.relative_to(rendered_path)
        rendered_content = render(str(original_j2_file))
        output_file = j2_file.with_suffix('')
        output_file.write_text(rendered_content)
        j2_file.unlink()

    return rendered_dir

def main():
    parser = argparse.ArgumentParser(description="Render challenge templates")
    parser.add_argument("template", help="Template file or directory to render")
    parser.add_argument("output", nargs='?', help="Output file or directory (optional)", default=None)
    args = parser.parse_args()

    template_path = pathlib.Path(args.template)

    if template_path.is_dir():
        rendered_dir = render_challenge(args.template, output_dir=args.output)
        print(f"Rendered challenge directory: {rendered_dir}")
    elif template_path.is_file() and template_path.suffix == ".j2":
        rendered_content = render(args.template)
        if args.output:
            pathlib.Path(args.output).write_text(rendered_content)
            print(f"Rendered to: {args.output}")
        else:
            print(rendered_content)
    else:
        print(f"Error: {args.template} must be a directory or a .j2 template file")
        sys.exit(1)

if __name__ == "__main__":
    main()
