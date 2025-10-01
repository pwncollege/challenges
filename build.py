#!/bin/env python3

import subprocess
import textwrap
import argparse
import pyastyle
import pathlib
import random
import shutil
import jinja2
import base64
import black
import shlex
import glob
import sys
import os
import re

class ChallengeRandom(random.Random):
    pass

def layout_text(text):
    return "\n".join(f'puts("{line}");' for line in textwrap.wrap(textwrap.dedent(text), width=120))

@jinja2.pass_context
def layout_text_walkthrough(context, text):
    return layout_text(text) if not context.get("walkthrough") or context.get("challenge.walkthrough") else "\n"

def render(template, seed):
    env = jinja2.Environment(loader=jinja2.FileSystemLoader(template.parents))
    env.filters.update({ "layout_text": layout_text, "layout_text_walkthrough": layout_text_walkthrough })
    rendered = env.get_template(template.name).render(random=ChallengeRandom(seed), trim_blocks=True, lstrip_blocks=True)
    try:
        if ".py" in template.suffixes or "python" in rendered.splitlines()[0]:
            return black.format_str(rendered, mode=black.FileMode(line_length=120))
        elif ".c" in template.suffixes:
            return re.sub("\n{2,}", "\n\n", pyastyle.format(rendered, "--style=allman"))
    except black.parsing.InvalidInput as e:
        print(f"WARNING: template {template} does not format properly: {e}")
    return rendered

def render_challenge(template_dir, seed, output_dir=None):
    rendered_dir = output_dir or pathlib.Path(f"/tmp/pwncollege-{template_dir.name}-{os.urandom(4).hex()}")
    shutil.copytree(template_dir, rendered_dir)
    if (rendered_dir/"challenge").exists() and not (dockerfile_path := rendered_dir/"challenge/Dockerfile").exists():
        dockerfile_path.write_text(render(pathlib.Path(__file__).parent/"base_templates/default-dockerfile.j2", seed))

    for src_j2_file in template_dir.rglob("*.j2"):
        output_file = (dst_j2_file := rendered_dir/src_j2_file.relative_to(template_dir)).with_suffix('')
        output_file.write_text(render(src_j2_file, seed))
        output_file.chmod(src_j2_file.stat().st_mode)
        dst_j2_file.unlink()

    return rendered_dir

def test_challenge(challenge_dir, seed, image_name=None):
    image_name = image_name or challenge_dir.name
    temp_flag = pathlib.Path(f"/tmp/pwncollege-{image_name}-flag")
    temp_flag.write_text("pwn.college{"+base64.b64encode(os.urandom(40)).decode()+"}")

    try:
        subprocess.check_call(["docker", "build", "-t", image_name, challenge_dir/"challenge"])
        for test_file in glob.glob(str(challenge_dir/"test*/test_*")):
            container = subprocess.check_output([
                "docker", "run", "--rm", "-id",
                "--name", f"""{image_name}-{re.sub("[^a-zA-Z0-9-]", "", os.path.basename(test_file))}""",
                "-v", f"{challenge_dir}:{challenge_dir}:ro", "-v", f"{temp_flag}:/flag:ro",
                image_name, "sh", "-c", "read forever"
            ]).decode().strip()
            subprocess.check_call(["docker", "exec", container, "sh", "-c", "[ ! -e /challenge/.init ] || /challenge/.init"])
            subprocess.check_call([
                "docker", "exec", "-u", "1000:1000", "-e", f"FLAG={temp_flag.read_text()}", "-e", f"SEED={seed}", container, test_file
            ])
            print(f"PASSED: {test_file}")
            subprocess.check_output(["docker", "kill", container])
    except subprocess.CalledProcessError as e:
        print(f"FAILED: {shlex.join(e.cmd)}")
        return False
    return True

def main():
    parser = argparse.ArgumentParser(description="Render challenge templates")
    parser.add_argument("challenge", help="Challenge directory to build/test", type=pathlib.Path)
    parser.add_argument("--output-dir", help="Output file or directory", type=pathlib.Path)
    parser.add_argument("--no-test", action="store_true", help="Don't test the challenge (by building Docker image and running tests)")
    parser.add_argument("--seed", action="store", help="The random seed for templating", default=None, type=int)
    parser.add_argument("--image-name", help="Docker image name to use for testing (default: directory name)")
    args = parser.parse_args()

    if args.challenge.is_file():
        print(render(args.challenge, seed=args.seed))
        return 0

    seed = random.randrange(2**64) if args.seed is None else args.seed
    rendered_dir = render_challenge(args.challenge, seed, output_dir=args.output_dir)
    print(f"Rendered to: {rendered_dir}")
    return 0 if args.no_test or test_challenge(rendered_dir, seed, image_name=args.image_name) else 1

if __name__ == "__main__":
    sys.exit(main())
