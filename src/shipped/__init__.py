"""shipped — Release management CLI.

Bump versions, generate changelogs from git history, tag releases,
and publish to GitHub + PyPI. One command to ship.
"""

from shipped.version import Version, bump_version
from shipped.changelog import generate_changelog
from shipped.gitops import create_tag, push_tag, get_last_tag, get_commits_since_tag
from shipped.publisher import publish_pypi

__all__ = [
    "Version",
    "bump_version",
    "generate_changelog",
    "create_tag",
    "push_tag",
    "get_last_tag",
    "get_commits_since_tag",
    "publish_pypi",
]