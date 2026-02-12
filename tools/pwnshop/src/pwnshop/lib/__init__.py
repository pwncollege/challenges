import base64
import contextlib
import logging
import os
import pathlib
import random
import re
import shutil
import subprocess
import tempfile
from typing import Iterable, Iterator, List, Optional, Sequence

import black
import jinja2
import pyastyle

logger = logging.getLogger(__name__)

CHALLENGE_SEED = int(os.environ.get("CHALLENGE_SEED", "0"))

def _find_git_root(start: pathlib.Path) -> pathlib.Path:
    """
    Walk upwards from *start* (file or dir) to find a git worktree root.

    Git worktrees store `.git` as a file, not a directory, so we only check for
    existence.
    """

    start = pathlib.Path(start)
    if start.is_file():
        start = start.parent
    for candidate in (start, *start.parents):
        if (candidate / ".git").exists():
            return candidate
    raise FileNotFoundError(f"Could not locate git root from {start}")


class RelativeEnvironment(jinja2.Environment):
    def join_path(self, template: str, parent: str) -> str:
        return str(pathlib.PurePosixPath(parent).parent / template)


def render(template: pathlib.Path) -> str:
    logger.debug("rendering template %s (seed=%d)", template, CHALLENGE_SEED)
    template = pathlib.Path(template).resolve()
    git_root = _find_git_root(template)
    challenges_root = git_root / "challenges"
    try:
        template_name = template.relative_to(challenges_root).as_posix()
    except ValueError as e:
        raise FileNotFoundError(f"Template {template} is not under {challenges_root}") from e

    env = RelativeEnvironment(loader=jinja2.FileSystemLoader(challenges_root))
    try:
        rendered = env.get_template(template_name).render(
            random=random.Random(CHALLENGE_SEED), trim_blocks=True, lstrip_blocks=True
        )
    except jinja2.TemplateNotFound as e:
        logger.error("template %s: could not find referenced template %r", template, str(e))
        raise RuntimeError(f"Template {template}: could not find {e!r}") from e
    try:
        if ".py" in template.suffixes or "python" in rendered.splitlines()[0]:
            logger.debug("formatting %s as python with black", template)
            return black.format_str(rendered, mode=black.FileMode(line_length=120))
        if ".c" in template.suffixes:
            logger.debug("formatting %s as C with astyle", template)
            return re.sub("\n{2,}", "\n\n", pyastyle.format(rendered, "--style=allman"))
    except black.parsing.InvalidInput as error:
        logger.warning("template %s does not format properly: %s", template, error)
    return rendered


def render_challenge(template_directory: pathlib.Path) -> pathlib.Path:
    logger.info("rendering challenge %s", template_directory)
    rendered_directory = pathlib.Path(tempfile.mkdtemp(prefix="pwncollege-"))
    logger.debug("render output directory: %s", rendered_directory)

    def ignore_git_crypt(current, names):
        ignored = {
            name
            for name in names
            if (path := pathlib.Path(current) / name).is_file()
            and path.open("rb").read(16).startswith(b"\x00GITCRYPT\x00")
        }
        if ignored:
            logger.debug("skipping git-crypt encrypted files: %s", ignored)
        return ignored

    shutil.copytree(template_directory, rendered_directory, dirs_exist_ok=True, ignore=ignore_git_crypt)
    templates = list(path.relative_to(rendered_directory) for path in rendered_directory.rglob("*.j2"))
    logger.debug("found %d template(s) to render", len(templates))
    for path in templates:
        destination = (rendered_directory / path).with_suffix("")
        logger.debug("rendering %s -> %s", path, destination.name)
        destination.write_text(render(template_directory / path))
        destination.chmod((template_directory / path).stat().st_mode)
        (rendered_directory / path).unlink()
    return rendered_directory


@contextlib.contextmanager
def run_challenge(
    challenge_image: str, *, volumes: Optional[Sequence[pathlib.Path]] = None
) -> Iterator[tuple[str, str]]:
    flag = "pwn.college{" + base64.b64encode(os.urandom(32)).decode() + "}"
    env_options = []
    for key, value in {
        "FLAG": flag,
        "SEED": str(CHALLENGE_SEED),
        "PATH": "/challenge/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
    }.items():
        env_options.extend(["--env", f"{key}={value}"])
    logger.info("starting container for image %s", challenge_image)
    if volumes:
        logger.debug("mounting volumes: %s", volumes)
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
                "--runtime=" + os.environ.get("PWN_CHALLENGE_RUNTIME", "runc"),
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
    logger.debug("container started: %s", container[:12])
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
    logger.debug("flag written to /flag")
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
    logger.debug(".init completed (if present)")
    try:
        yield container, flag
    finally:
        logger.debug("killing container %s", container[:12])
        subprocess.run(
            ["docker", "kill", container],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )


def build_challenge(challenge_path: pathlib.Path) -> str:
    logger.info("building challenge %s", challenge_path)
    rendered_directory = render_challenge(challenge_path)
    try:
        label = challenge_path.as_posix().removeprefix("challenges/")
        logger.debug("docker build context: %s", rendered_directory / "challenge")
        image_id = subprocess.check_output(
            [
                "docker",
                "build",
                "-q",
                "--label",
                f"pwncollege.challenge={label}",
                str(rendered_directory / "challenge"),
            ],
            text=True,
        ).strip()
        logger.info("built image %s for %s", image_id[:19], challenge_path)
        return image_id
    except subprocess.CalledProcessError as error:
        logger.error("docker build failed for %s", challenge_path)
        raise RuntimeError(f"Failed to build challenge {challenge_path}") from error
    finally:
        shutil.rmtree(rendered_directory, ignore_errors=True)


def list_challenges(directory: pathlib.Path, modified_since: Optional[str] = None) -> List[pathlib.Path]:
    directory = pathlib.Path(directory)
    logger.debug("listing challenges in %s", directory)
    candidate_dirs = [
        challenge_dir.parent.relative_to(directory)
        for challenge_dir in directory.glob("**/challenge")
        if challenge_dir.is_dir()
    ]
    ancestors = {parent.as_posix() for path in candidate_dirs for parent in path.parents if parent.as_posix() != "."}
    challenge_dirs = sorted(
        [path for path in candidate_dirs if path.as_posix() not in ancestors],
        key=lambda path: len(path.parts),
        reverse=True,
    )
    challenges = list(challenge_dirs)
    logger.debug("found %d challenge(s) in %s", len(challenges), directory)
    if not modified_since:
        return challenges

    relative_lookup = {path.as_posix(): path for path in challenge_dirs}
    logger.debug("filtering by git diff --name-only --relative %s", modified_since)
    diff_output = subprocess.check_output(
        ["git", "diff", "--name-only", "--relative", modified_since],
        cwd=directory,
        text=True,
    )
    affected = set()
    for line in diff_output.splitlines():
        relative_line = line.strip()
        if not relative_line:
            continue
        path = pathlib.PurePosixPath(relative_line)
        relative_path = path
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
    logger.debug("modified-since filter: %d affected challenge(s)", len(affected))
    return sorted((relative_lookup[item] for item in affected), key=lambda path: len(path.parts), reverse=True)


def resolve_targets(targets: Iterable[pathlib.Path], *, modified_since: Optional[str] = None) -> List[pathlib.Path]:
    return [
        target / challenge_path
        for target in targets
        for challenge_path in list_challenges(target, modified_since=modified_since)
    ]
