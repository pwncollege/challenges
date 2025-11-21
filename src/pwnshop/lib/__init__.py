import base64
import contextlib
import os
import pathlib
import random
import re
import shutil
import subprocess
import sys
from collections import defaultdict

import black
import jinja2
import pyastyle

REPOSITORY_ROOT = pathlib.Path(__file__).resolve().parents[3]
DEFAULT_DOCKERFILE_PATH = REPOSITORY_ROOT / "challenges/common/default-dockerfile.j2"
CHALLENGE_SEED = int(os.environ.get("CHALLENGE_SEED", "0"))


def render(template):
    env = jinja2.Environment(loader=jinja2.FileSystemLoader(template.parents))
    rendered = env.get_template(template.name).render(
        random=random.Random(CHALLENGE_SEED), trim_blocks=True, lstrip_blocks=True
    )
    try:
        if ".py" in template.suffixes or "python" in rendered.splitlines()[0]:
            return black.format_str(rendered, mode=black.FileMode(line_length=120))
        if ".c" in template.suffixes:
            return re.sub("\n{2,}", "\n\n", pyastyle.format(rendered, "--style=allman"))
    except black.parsing.InvalidInput as error:
        print(f"WARNING: template {template} does not format properly: {error}", file=sys.stderr)
    return rendered


def render_challenge(template_directory):
    try:
        challenge_name = "-".join(
            template_directory.resolve().relative_to(REPOSITORY_ROOT / "challenges").parts
        )
    except ValueError as error:
        raise FileNotFoundError(f"Challenges must live under {REPOSITORY_ROOT / 'challenges'}") from error
    rendered_directory = pathlib.Path(f"/tmp/pwncollege-{challenge_name}-{os.urandom(4).hex()}")
    shutil.copytree(template_directory, rendered_directory)
    for path in (path.relative_to(template_directory) for path in template_directory.rglob("*.j2")):
        destination = (rendered_directory / path).with_suffix("")
        destination.write_text(render(template_directory / path))
        destination.chmod((template_directory / path).stat().st_mode)
        (rendered_directory / path).unlink()
    dockerfile_path = rendered_directory / "challenge" / "Dockerfile"
    if not dockerfile_path.exists():
        dockerfile_path.write_text(render(DEFAULT_DOCKERFILE_PATH))
    return rendered_directory


@contextlib.contextmanager
def run_challenge(challenge_image, *, volumes=None):
    flag = "pwn.college{" + base64.b64encode(os.urandom(40)).decode() + "}"
    env_options = []
    for key, value in {"FLAG": flag, "SEED": str(CHALLENGE_SEED)}.items():
        env_options.extend(["--env", f"{key}={value}"])
    container = (
        subprocess.check_output(
            [
                "docker",
                "run",
                "--rm",
                "--interactive",
                "--detach",
                "--init",
                "--user=0:0",
                "--device=/dev/kvm",
                "--cap-add=SYS_PTRACE",
                *env_options,
                *[f"--volume={volume}:{volume}:ro" for volume in (volumes or [])],
                challenge_image,
                "/bin/sh",
                "-c",
                "read forever",
            ]
        )
        .decode()
        .strip()
    )
    subprocess.run(
        [
            "docker",
            "exec",
            "--interactive",
            "--user=0:0",
            container,
            "/bin/sh",
            "-c",
            "cat >/flag && chown 0:0 /flag && chmod 0400 /flag",
        ],
        input=f"{flag}\n",
        text=True,
        check=True,
    )
    subprocess.check_call(
        [
            "docker",
            "exec",
            "--user=0:0",
            container,
            "/bin/sh",
            "-c",
            "[ ! -e /challenge/.init ] || /challenge/.init",
        ]
    )
    try:
        yield container, flag
    finally:
        subprocess.run(
            ["docker", "kill", container],
            stdout=subprocess.DEVNULL,
            check=True,
        )


def resolve_path(path_argument):
    raw = path_argument.as_posix() if isinstance(path_argument, pathlib.Path) else str(path_argument)
    if raw.startswith("default/"):
        raw = raw[len("default/") :]
    raw_path = pathlib.Path(raw)
    candidate_order = [
        raw_path,
        (REPOSITORY_ROOT / raw_path),
        (REPOSITORY_ROOT / "challenges" / raw_path),
    ]
    for candidate in candidate_order:
        if candidate.exists():
            return candidate.resolve()
    search_target = raw_path.as_posix().strip("/")
    if search_target and "/" not in search_target:
        raise FileNotFoundError(
            "Challenge references must include a module (e.g., module/challenge). "
            f"Got: {path_argument}"
        )
    raise FileNotFoundError(f"No such file or directory: {path_argument}")


def build_challenge(challenge_path):
    rendered_directory = render_challenge(challenge_path)
    try:
        image_id = (
            subprocess.check_output(
                ["docker", "build", "-q", str(rendered_directory / "challenge")],
                text=True,
            )
            .strip()
        )
        return image_id
    except subprocess.CalledProcessError as error:
        raise RuntimeError(f"Failed to build challenge {challenge_path}") from error
    finally:
        shutil.rmtree(rendered_directory, ignore_errors=True)


def discover_challenges(modified_since=None):
    challenges_directory = REPOSITORY_ROOT / "challenges"
    group_directories = sorted(
        [
            attr_file.parent.relative_to(challenges_directory)
            for attr_file in challenges_directory.rglob(".gitattributes")
        ],
        key=lambda path: len(path.parts),
        reverse=True,
    )
    candidate_dirs = [
        challenge_dir.parent.relative_to(challenges_directory)
        for challenge_dir in challenges_directory.glob("**/challenge")
    ]
    ancestors = {
        parent.as_posix()
        for path in candidate_dirs
        for parent in path.parents
    }
    challenge_dirs = sorted(
        [path for path in candidate_dirs if path.as_posix() not in ancestors],
        key=lambda path: len(path.parts),
        reverse=True,
    )
    grouped = defaultdict(list)
    relative_lookup = {}
    for challenge_dir in challenge_dirs:
        relative = challenge_dir.as_posix()
        group = "default"
        challenge_name = relative
        for candidate in group_directories:
            if not challenge_dir.is_relative_to(candidate):
                continue
            remainder = challenge_dir.relative_to(candidate)
            if remainder.parts:
                group = candidate.as_posix()
                challenge_name = remainder.as_posix()
                break
        grouped[group].append(challenge_name)
        relative_lookup[relative] = (group, challenge_name)
    if modified_since:
        diff_output = subprocess.check_output(
            ["git", "diff", "--name-only", modified_since],
            cwd=REPOSITORY_ROOT,
            text=True,
        )
        prefix = pathlib.PurePosixPath("challenges")
        affected = set()
        for line in diff_output.splitlines():
            relative_line = line.strip()
            if not relative_line:
                continue
            path = pathlib.PurePosixPath(relative_line)
            if not path.is_relative_to(prefix):
                continue
            relative_path = path.relative_to(prefix)
            candidate = relative_path
            while True:
                candidate_key = candidate.as_posix()
                if candidate_key in relative_lookup:
                    affected.add(candidate_key)
                    break
                if len(candidate.parts) <= 1:
                    break
                candidate = candidate.parent
            parts = relative_path.parts
            if len(parts) > 1 and "common" in parts[1:]:
                common_index = parts.index("common", 1)
                ancestor = pathlib.PurePosixPath(*parts[:common_index]).as_posix()
                for key in relative_lookup:
                    if key.startswith(ancestor + "/"):
                        affected.add(key)
        filtered = defaultdict(list)
        for key in affected:
            group, challenge_name = relative_lookup[key]
            filtered[group].append(challenge_name)
        grouped = filtered
    for group in grouped:
        grouped[group].sort()
    return dict(sorted(grouped.items()))
