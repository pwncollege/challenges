import pathlib
import shutil

import click
from rich.console import Console
from rich.syntax import Syntax

from .. import lib

console = Console()


def _print_contents(path: pathlib.Path, contents: str):
    language_map = {
        ".py": "python",
        ".sh": "bash",
        ".bash": "bash",
        ".zsh": "bash",
        ".c": "c",
        ".h": "c",
        ".cxx": "cpp",
        ".cpp": "cpp",
        ".cc": "cpp",
        ".js": "javascript",
        ".ts": "typescript",
        ".dockerfile": "docker",
        ".json": "json",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".toml": "toml",
        ".md": "markdown",
        ".html": "html",
        ".htm": "html",
        ".css": "css",
        ".go": "go",
        ".rs": "rust",
        ".java": "java",
        ".rb": "ruby",
        ".php": "php",
        ".sql": "sql",
        ".txt": "text",
    }
    language = language_map.get(path.suffix.lower())
    if not language and path.name.lower() == "dockerfile":
        language = "docker"
    if not language and contents.startswith("#!"):
        shebang = contents.splitlines()[0]
        if "python" in shebang:
            language = "python"
        elif "bash" in shebang or "sh" in shebang:
            language = "bash"
    console.print(
        Syntax(contents, language, theme="ansi_light", word_wrap=False) if language else contents,
        highlight=not bool(language),
    )


@click.command("render")
@click.argument(
    "targets",
    nargs=-1,
    required=True,
    type=click.Path(path_type=pathlib.Path, exists=True, dir_okay=True, file_okay=True, resolve_path=False),
)
@click.option(
    "--output",
    "output_path",
    type=click.Path(path_type=pathlib.Path, file_okay=True, dir_okay=True, writable=True, resolve_path=False),
    help="Write rendered output to this path (file or directory). Defaults to stdout.",
)
@click.option("--modified-since", metavar="REF", help="Only include challenges changed versus REF.")
def render_command(targets, output_path, modified_since):
    """Render one or more challenges."""
    if output_path and len(targets) != 1:
        raise click.ClickException("--output requires a single target")

    file_targets = [target for target in targets if target.is_file()]
    directory_targets = [target for target in targets if target.is_dir()]

    if output_path:
        target = targets[0]
        if target.is_file():
            rendered_contents = lib.render(target)
            if output_path.exists() and output_path.is_dir():
                raise click.ClickException("--output points to a directory while rendering a file")
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(rendered_contents)
            console.print(f"[green]Wrote[/] {output_path}")
            return
        if not (challenge_paths := lib.resolve_targets([target], modified_since=modified_since)):
            if modified_since:
                console.print(f"[yellow]No challenges found since {modified_since}[/]")
                return
            raise click.ClickException("No challenges found in provided targets.")
        if len(challenge_paths) != 1:
            raise click.ClickException("--output requires a single challenge target")
        challenge_path = challenge_paths[0]
        try:
            rendered_directory = lib.render_challenge(challenge_path)
        except FileNotFoundError as error:
            raise click.ClickException(str(error)) from error
        if output_path.exists():
            raise click.ClickException(f"Refusing to overwrite existing path: {output_path}")
        shutil.copytree(rendered_directory, output_path)
        shutil.rmtree(rendered_directory)
        console.print(f"[green]Rendered[/] {output_path}")
        return

    for file_target in file_targets:
        rendered_contents = lib.render(file_target)
        console.rule(str(file_target))
        _print_contents(file_target, rendered_contents)

    challenge_paths = lib.resolve_targets(directory_targets, modified_since=modified_since)
    if not challenge_paths and directory_targets:
        if modified_since:
            console.print(f"[yellow]No challenges found since {modified_since}[/]")
            return
        raise click.ClickException("No challenges found in provided targets.")
    for challenge_path in challenge_paths:
        try:
            rendered_directory = lib.render_challenge(challenge_path)
        except FileNotFoundError as error:
            raise click.ClickException(str(error)) from error
        try:
            files = sorted(path for path in rendered_directory.rglob("*") if path.is_file())
            if not files:
                console.print("[yellow]Rendered challenge has no files[/]")
            console.rule(str(challenge_path))
            for file_path in files:
                relative = file_path.relative_to(rendered_directory)
                console.rule(str(relative))
                try:
                    contents = file_path.read_text()
                except UnicodeDecodeError:
                    size = file_path.stat().st_size
                    console.print(f"[yellow]Binary file ({size} bytes)[/]")
                    continue
                _print_contents(file_path, contents)
        finally:
            shutil.rmtree(rendered_directory, ignore_errors=True)
