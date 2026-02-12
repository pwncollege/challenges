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
import yaml

logger = logging.getLogger(__name__)

CHALLENGE_SEED = int(os.environ.get("CHALLENGE_SEED", "0"))


class _NoSelfExtendLoader(jinja2.FileSystemLoader):
    """FileSystemLoader that prevents templates from extending/including themselves.

    When search paths overlap (e.g. parent directories containing identically-named
    subdirectories), ``computing-101/common/Dockerfile.j2`` extending
    ``common/Dockerfile.j2`` can resolve back to itself.  This loader cooperates
    with :class:`_NoSelfExtendEnv` (which overrides ``join_path``) to give each
    extends/include reference a unique name encoding which physical file to skip.
    """

    def __init__(self, searchpath, **kwargs):
        super().__init__(searchpath, **kwargs)
        self._name_to_realpath = {}
        self._skip_registry = {}
        self._counter = 0

    def get_source(self, environment, template):
        if template in self._skip_registry:
            skip_realpath, actual_name = self._skip_registry[template]
        else:
            skip_realpath, actual_name = None, template

        for searchpath in self.searchpath:
            filename = os.path.join(os.fspath(searchpath), *actual_name.split("/"))
            if not os.path.isfile(filename):
                continue
            realpath = os.path.realpath(filename)
            if realpath == skip_realpath:
                continue

            self._name_to_realpath[template] = realpath
            with open(filename, encoding=self.encoding) as f:
                contents = f.read()
            mtime = os.path.getmtime(filename)

            def uptodate(fn=filename, mt=mtime):
                try:
                    return os.path.getmtime(fn) == mt
                except OSError:
                    return False

            return contents, filename, uptodate

        raise jinja2.TemplateNotFound(actual_name)

    def make_skip_name(self, template, parent_name):
        """Return a unique template name that skips the physical file *parent_name* resolved to."""
        realpath = self._name_to_realpath.get(parent_name)
        if not realpath:
            return template
        self._counter += 1
        unique = f"\x00skip{self._counter}\x00{template}"
        self._skip_registry[unique] = (realpath, template)
        return unique


class _NoSelfExtendEnv(jinja2.Environment):
    """Jinja2 environment that prevents circular template inheritance from overlapping search paths."""

    def join_path(self, template, parent):
        if isinstance(self.loader, _NoSelfExtendLoader):
            return self.loader.make_skip_name(template, parent)
        return template


def render(template: pathlib.Path) -> str:
    logger.debug("rendering template %s (seed=%d)", template, CHALLENGE_SEED)
    env = _NoSelfExtendEnv(loader=_NoSelfExtendLoader(template.parents))
    try:
        rendered = env.get_template(template.name).render(
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
    challenge_image: str,
    *,
    challenge_path: Optional[pathlib.Path] = None,
    volumes: Optional[Sequence[pathlib.Path]] = None,
) -> Iterator[tuple[str, str]]:
    flag = "pwn.college{" + base64.b64encode(os.urandom(32)).decode() + "}"
    privileged = ((yaml.safe_load(challenge_yml.read_text()) or {}).get("privileged") is True) if challenge_path and (challenge_yml := challenge_path / "challenge.yml").is_file() else False
    runtime = "kata" if privileged else os.environ.get("PWN_CHALLENGE_RUNTIME", "runc")
    runtime_options = [
        "--device=/dev/kvm",
        "--device=/dev/net/tun",
        "--runtime=" + runtime,
        "--cap-add=SYS_PTRACE",
        "--sysctl=net.ipv4.ip_unprivileged_port_start=1024",
    ]
    if privileged:
        runtime_options.extend(["--cap-add=SYS_ADMIN", "--cap-add=NET_ADMIN"])
    env_options = []
    for key, value in {
        "FLAG": flag,
        "SEED": str(CHALLENGE_SEED),
        "PATH": "/challenge/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
    }.items():
        env_options.extend(["--env", f"{key}={value}"])
    logger.info("starting container for image %s", challenge_image)
    logger.debug("container runtime options for %s: %s", challenge_path or "<none>", runtime_options)
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
                *runtime_options,
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
