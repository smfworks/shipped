"""shipped CLI — Release management from the terminal.

Commands:
  shipped bump <major|minor|patch>  — Bump version in pyproject.toml
  shipped changelog                 — Generate changelog from git history
  shipped tag                        — Create a git tag for the current version
  shipped push                       — Push the tag to the remote
  shipped publish                    — Build and upload to PyPI
  shipped release <major|minor|patch> — Bump + changelog + tag + push (full release)
  shipped current                    — Show current version
"""

from __future__ import annotations

import sys
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from shipped.version import (
    Version,
    bump_version,
    read_version_from_pyproject,
    write_version_to_pyproject,
)
from shipped.changelog import generate_changelog
from shipped.gitops import (
    get_repo,
    get_last_tag,
    get_commits_since_tag,
    create_tag,
    push_tag,
)
from shipped.publisher import publish_pypi

console = Console()


def _load_version(config: str | None) -> Version:
    """Load current version from pyproject.toml."""
    path = Path(config) if config else None
    try:
        return read_version_from_pyproject(path)
    except FileNotFoundError:
        console.print("[red]Error:[/red] pyproject.toml not found.")
        raise SystemExit(1)
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise SystemExit(1)


@click.group()
@click.option("--config", default=None, help="Path to pyproject.toml")
@click.pass_context
def cli(ctx: click.Context, config: str | None) -> None:
    """shipped — Release management CLI."""
    ctx.ensure_object(dict)
    ctx.obj["config"] = config


@cli.command()
@click.argument("part", type=click.Choice(["major", "minor", "patch"]))
@click.pass_context
def bump(ctx: click.Context, part: str) -> None:
    """Bump the project version (major, minor, or patch)."""
    config = ctx.obj.get("config")
    current = _load_version(config)
    new = bump_version(current, part)

    path = Path(config) if config else None
    write_version_to_pyproject(new, path)

    console.print(
        Panel(
            Text.from_markup(
                f"[dim]{current}[/dim] → [bold cyan]{new}[/bold cyan]"
            ),
            title="Version Bumped",
            border_style="cyan",
        )
    )


@cli.command()
@click.option("--output", "-o", default=None, help="Write changelog to file instead of stdout")
@click.pass_context
def changelog(ctx: click.Context, output: str | None) -> None:
    """Generate a changelog from git history since the last tag."""
    config = ctx.obj.get("config")
    current = _load_version(config)

    try:
        repo = get_repo()
    except RuntimeError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise SystemExit(1)

    last_tag = get_last_tag(repo)
    commits = get_commits_since_tag(repo, last_tag)

    if not commits:
        console.print("[yellow]No commits found since last tag.[/yellow]")
        return

    md = generate_changelog(commits, str(current), previous_version=last_tag)

    if output:
        Path(output).write_text(md + "\n")
        console.print(f"[green]Changelog written to[/green] {output}")
    else:
        console.print(md)


@cli.command()
@click.option("--message", "-m", default="", help="Tag annotation message")
@click.pass_context
def tag(ctx: click.Context, message: str) -> None:
    """Create a git tag for the current version."""
    config = ctx.obj.get("config")
    current = _load_version(config)

    try:
        repo = get_repo()
    except RuntimeError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise SystemExit(1)

    tag_name = create_tag(repo, str(current), message=message)
    console.print(f"[green]Tag created:[/green] [bold cyan]{tag_name}[/bold cyan]")


@cli.command()
@click.option("--remote", default="origin", help="Git remote name")
@click.pass_context
def push(ctx: click.Context, remote: str) -> None:
    """Push the current version tag to the remote."""
    config = ctx.obj.get("config")
    current = _load_version(config)

    try:
        repo = get_repo()
    except RuntimeError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise SystemExit(1)

    tag_name = f"v{current}"
    try:
        push_tag(repo, tag_name, remote=remote)
        console.print(f"[green]Pushed tag[/green] [bold cyan]{tag_name}[/bold cyan] → {remote}")
    except Exception as e:
        console.print(f"[red]Push failed:[/red] {e}")
        raise SystemExit(1)


@cli.command()
@click.option("--test", is_flag=True, help="Publish to TestPyPI instead of PyPI")
@click.pass_context
def publish(ctx: click.Context, test: bool) -> None:
    """Build and upload the package to PyPI."""
    config = ctx.obj.get("config")
    path = Path(config).parent if config else None

    try:
        result = publish_pypi(directory=path, test=test)
        console.print(f"[green]{result}[/green]")
    except RuntimeError as e:
        console.print(f"[red]Publish failed:[/red] {e}")
        raise SystemExit(1)


@cli.command()
@click.argument("part", type=click.Choice(["major", "minor", "patch"]))
@click.option("--test", is_flag=True, help="Publish to TestPyPI instead of PyPI")
@click.option("--remote", default="origin", help="Git remote name")
@click.option("--changelog-output", "-o", default="CHANGELOG.md", help="Changelog output file")
@click.pass_context
def release(ctx: click.Context, part: str, test: bool, remote: str, changelog_output: str) -> None:
    """Full release: bump + changelog + tag + push + publish."""
    config = ctx.obj.get("config")
    current = _load_version(config)
    new = bump_version(current, part)

    # 1. Bump version
    path = Path(config) if config else None
    write_version_to_pyproject(new, path)
    console.print(f"[dim]{current}[/dim] → [bold cyan]{new}[/bold cyan]")

    # 2. Generate changelog
    try:
        repo = get_repo()
    except RuntimeError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise SystemExit(1)

    last_tag = get_last_tag(repo)
    commits = get_commits_since_tag(repo, last_tag)

    if commits:
        md = generate_changelog(commits, str(new), previous_version=last_tag)
        # Prepend to changelog file
        changelog_path = Path(changelog_output)
        existing = changelog_path.read_text() if changelog_path.exists() else ""
        changelog_path.write_text(md + "\n" + existing)
        console.print(f"[green]Changelog written to[/green] {changelog_output}")

    # 3. Commit the version bump
    repo.index.add(["pyproject.toml"])
    if commits and Path(changelog_output).exists():
        repo.index.add([changelog_output])
    repo.index.commit(f"chore: release v{new}")

    # 4. Create tag
    tag_name = create_tag(repo, str(new), message=f"Release v{new}")
    console.print(f"[green]Tag created:[/green] [bold cyan]{tag_name}[/bold cyan]")

    # 5. Push commit + tag
    try:
        repo.remote(remote).push()
        push_tag(repo, tag_name, remote=remote)
        console.print(f"[green]Pushed[/green] [bold cyan]{tag_name}[/bold cyan] → {remote}")
    except Exception as e:
        console.print(f"[red]Push failed:[/red] {e}")
        console.print("[yellow]Tag created locally but not pushed. Fix push manually.[/yellow]")
        raise SystemExit(1)

    # 6. Publish to PyPI
    if not test:
        try:
            result = publish_pypi(directory=path)
            console.print(f"[green]{result}[/green]")
        except RuntimeError as e:
            console.print(f"[red]Publish failed:[/red] {e}")
            console.print("[yellow]Tag pushed but PyPI upload failed. Run 'shipped publish' manually.[/yellow]")
            raise SystemExit(1)

    console.print(
        Panel(
            Text.from_markup(f"[bold green]Released v{new}[/bold green]"),
            border_style="green",
        )
    )


@cli.command()
@click.pass_context
def current(ctx: click.Context) -> None:
    """Show the current project version."""
    config = ctx.obj.get("config")
    version = _load_version(config)
    console.print(f"[bold cyan]{version}[/bold cyan]")


if __name__ == "__main__":
    cli()