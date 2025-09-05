#!/bin/env python3

import subprocess
import tempfile
import argparse
import pyastyle
import logging
import pathlib
import random
import shutil
import jinja2
import black
import glob
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

def test_challenge(rendered_challenge_dir, image_name=None):
    image_name = image_name or os.path.basename(rendered_challenge_dir)
    if not os.path.exists(rendered_challenge_dir + "/src/Dockerfile"):
        shutil.copy2(os.path.dirname(__file__) + "/default-dockerfile", rendered_challenge_dir + "/src/Dockerfile")

    src_dir = os.path.join(rendered_challenge_dir, "src")
    print(f"Building Docker image: {image_name}")
    result = subprocess.run(["docker", "build", "-t", image_name, src_dir], capture_output=False, check=False)
    if result.returncode != 0:
        print("ERROR: Docker build failed")
        return False

    for test_file in glob.glob(rendered_challenge_dir + "/test*/test_*"):
        result = subprocess.run([
            "docker", "run", "--rm",
            "-v", f"{rendered_challenge_dir}:{rendered_challenge_dir}:ro",
            image_name,
            "/bin/sh", test_file
        ], capture_output=False, check=False)

        if result.returncode == 0:
            print(f"PASSED: {test_file} passed")
        else:
            print(f"FAILED: {test_file} failed (exit code: {result.returncode})")
            return False

    return True

def main():
    parser = argparse.ArgumentParser(description="Render challenge templates")
    parser.add_argument("challenge_dir", help="Challenge directory to build/test")
    parser.add_argument("--output-dir", help="Output file or directory")
    parser.add_argument("--test", action="store_true", help="Test the challenge by building Docker image and running tests")
    parser.add_argument("--image-name", help="Docker image name to use for testing (default: directory name)")
    args = parser.parse_args()

    if os.path.isfile(args.challenge_dir):
        print(render(args.challenge_dir))
        return 0

    rendered_dir = render_challenge(args.challenge_dir, output_dir=args.output_dir)
    print(f"Rendered to: {rendered_dir}")
    if args.test:
        return 0 if test_challenge(rendered_dir, image_name=args.image_name) else 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
