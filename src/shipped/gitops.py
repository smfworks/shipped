"""Git operations for release management.

Tags, pushes, and queries git history using gitpython.
"""

from __future__ import annotations

from git import Repo, InvalidGitRepositoryError, TagObject
from pathlib import Path


def get_repo(path: Path | None = None) -> Repo:
    """Get a Repo object, raising if not in a git repo."""
    try:
        return Repo(path or ".")
    except InvalidGitRepositoryError:
        raise RuntimeError("Not a git repository. Run from a project root.")


def get_last_tag(repo: Repo) -> str | None:
    """Get the most recent tag name, or None if no tags exist."""
    tags = repo.tags
    if not tags:
        return None
    # Sort by commit date
    try:
        sorted_tags = sorted(
            tags,
            key=lambda t: t.commit.committed_datetime if isinstance(t.commit, TagObject) else t.commit.committed_datetime,
            reverse=True,
        )
        return sorted_tags[0].name if sorted_tags else None
    except Exception:
        # Fallback: just return the last tag
        return tags[-1].name if tags else None


def get_commits_since_tag(repo: Repo, tag: str | None = None) -> list[tuple[str, str]]:
    """Get (hash, message) tuples for commits since the given tag.

    If tag is None, returns all commits (first 200).
    """
    if tag:
        try:
            tag_commit = repo.tags[tag].commit
            commits = list(repo.iter_commits(f"{tag_commit.hexsha}..HEAD"))
        except (KeyError, Exception):
            commits = list(repo.iter_commits(max_count=200))
    else:
        commits = list(repo.iter_commits(max_count=200))

    return [(c.hexsha, c.message.strip()) for c in commits]


def create_tag(repo: Repo, version: str, message: str = "") -> str:
    """Create an annotated tag for the release. Returns the tag name."""
    tag_name = f"v{version}" if not version.startswith("v") else version
    if not message:
        message = f"Release {tag_name}"
    repo.create_tag(tag_name, message=message)
    return tag_name


def push_tag(repo: Repo, tag_name: str, remote: str = "origin") -> None:
    """Push a specific tag to the remote."""
    repo.remote(remote).push(tag_name)