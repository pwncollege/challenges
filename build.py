#!/bin/env python3

import subprocess
import argparse
import pyastyle
import pathlib
import random
import shutil
import jinja2
import base64
import black
import glob
import sys
import os
import re

class Challenge:
    def __init__(self, seed):
        self.random = random.Random(seed)

def render(template, seed):
    env = jinja2.Environment(loader=jinja2.FileSystemLoader(template.parents))
    rendered = env.get_template(template.name).render(challenge=Challenge(seed))
    try:
        if ".py" in template.suffixes or "python" in rendered.splitlines()[0]:
            return black.format_str(rendered, mode=black.FileMode(line_length=120))
        elif ".c" in template.suffixes:
            return re.sub("\n{2,}", "\n\n", pyastyle.format(rendered, "--style=allman"))
    except black.parsing.InvalidInput as e:
        print(f"WARNING: template {template} does not format properly: {e}")
    return rendered

def render_challenge(template_dir, output_dir=None, seed=None):
    rendered_dir = output_dir or pathlib.Path(f"/tmp/pwncollege-{template_dir.name}-{os.urandom(4).hex()}")
    seed = random.randrange(2**64) if seed is None else seed
    shutil.copytree(template_dir, rendered_dir)
    if (rendered_dir/"challenge").exists() and not (dockerfile_path := rendered_dir/"challenge/Dockerfile").exists():
        dockerfile_path.write_text(render(pathlib.Path(__file__).parent/"base_templates/default-dockerfile.j2", seed))

    for src_j2_file in template_dir.rglob("*.j2"):
        output_file = (dst_j2_file := rendered_dir/src_j2_file.relative_to(template_dir)).with_suffix('')
        output_file.write_text(render(src_j2_file, seed))
        output_file.chmod(src_j2_file.stat().st_mode)
        dst_j2_file.unlink()

    return rendered_dir

def test_challenge(challenge_dir, image_name=None):
    image_name = image_name or challenge_dir.name
    temp_flag = pathlib.Path(f"/tmp/pwncollege-{image_name}-flag")
    temp_flag.write_text("pwn.college{"+base64.b64encode(os.urandom(40)).decode()+"}")

    src_dir = os.path.join(challenge_dir, "challenge")
    result = subprocess.run(["docker", "build", "-t", image_name, src_dir], capture_output=False, check=False)
    if result.returncode != 0:
        print("ERROR: Docker build failed")
        return False

    for test_file in glob.glob(str(challenge_dir/"test*/test_*")):
        result = subprocess.run([
            "docker", "run", "--rm",
            "-v", f"{challenge_dir}:{challenge_dir}:ro",
            "-v", f"{temp_flag}:/flag:ro", "-e", f"FLAG={temp_flag.read_text()}",
            "--add-host", "challenge.localhost:127.0.0.1",
            "--add-host", "hacker.localhost:127.0.0.1",
            image_name, test_file
        ], capture_output=False, check=False)

        if result.returncode == 0:
            print(f"PASSED: {test_file} passed")
        else:
            print(f"FAILED: {test_file} failed (exit code: {result.returncode})")
            return False

    return True

def main():
    parser = argparse.ArgumentParser(description="Render challenge templates")
    parser.add_argument("challenge", help="Challenge directory to build/test", type=pathlib.Path)
    parser.add_argument("--output-dir", help="Output file or directory", type=pathlib.Path)
    parser.add_argument("--test", action="store_true", help="Test the challenge by building Docker image and running tests")
    parser.add_argument("--seed", action="store", help="The random seed for templating", default=None, type=int)
    parser.add_argument("--image-name", help="Docker image name to use for testing (default: directory name)")
    args = parser.parse_args()

    if args.challenge.is_file():
        print(render(args.challenge, seed=args.seed))
        return 0

    rendered_dir = render_challenge(args.challenge, output_dir=args.output_dir, seed=args.seed)
    print(f"Rendered to: {rendered_dir}")
    if args.test:
        return 0 if test_challenge(rendered_dir, image_name=args.image_name) else 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
