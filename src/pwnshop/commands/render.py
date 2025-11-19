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
@click.argument("target", type=str)
@click.option(
    "--output",
    "output_path",
    type=click.Path(path_type=pathlib.Path, file_okay=True, dir_okay=True, writable=True, resolve_path=False),
    help="Write rendered output to this path (file or directory). Defaults to stdout.",
)
def render_command(target, output_path):
    """Render a template file or an entire challenge directory."""
    try:
        target_path = lib.resolve_path(target)
    except FileNotFoundError as error:
        raise click.ClickException(str(error)) from error
    if target_path.is_file():
        rendered_contents = lib.render(target_path)
        if output_path:
            if output_path.exists() and output_path.is_dir():
                raise click.ClickException("--output points to a directory while rendering a file")
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(rendered_contents)
            console.print(f"[green]Wrote[/] {output_path}")
            return
        console.rule(str(target_path))
        _print_contents(target_path, rendered_contents)
        return
    try:
        rendered_directory = lib.render_challenge(target_path)
    except FileNotFoundError as error:
        raise click.ClickException(str(error)) from error
    if output_path:
        if output_path.exists():
            raise click.ClickException(f"Refusing to overwrite existing path: {output_path}")
        shutil.copytree(rendered_directory, output_path)
        shutil.rmtree(rendered_directory)
        console.print(f"[green]Rendered[/] {output_path}")
        return
    try:
        files = sorted(path for path in rendered_directory.rglob("*") if path.is_file())
        if not files:
            console.print("[yellow]Rendered challenge has no files[/]")
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


__all__ = ["render_command"]
