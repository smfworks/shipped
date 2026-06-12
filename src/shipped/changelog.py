"""Changelog generation from git history.

Parses conventional-commit-style messages and groups them into sections:
  feat:     → Features
  fix:      → Bug Fixes
  refactor: → Refactoring
  docs:     → Documentation
  chore:    → Chores
  Other     → Other Changes
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class ChangelogEntry:
    commit_hash: str
    message: str
    scope: str | None = None


@dataclass
class ChangelogSection:
    title: str
    entries: list[ChangelogEntry] = field(default_factory=list)


# Conventional commit pattern: type(scope): description
CONV_COMMIT_RE = re.compile(
    r"^(?P<type>[a-z]+)(?:\((?P<scope>[^)]+)\))?:\s*(?P<desc>.+)$"
)

SECTION_MAP = {
    "feat": "Features",
    "fix": "Bug Fixes",
    "refactor": "Refactoring",
    "docs": "Documentation",
    "chore": "Chores",
    "perf": "Performance",
    "test": "Tests",
    "ci": "CI",
    "build": "Build",
}

DEFAULT_SECTION = "Other Changes"


def parse_commit_message(message: str) -> tuple[str, str | None, str]:
    """Parse a conventional commit message. Returns (type, scope, description)."""
    first_line = message.strip().split("\n", 1)[0]
    m = CONV_COMMIT_RE.match(first_line)
    if m:
        return m.group("type"), m.group("scope"), m.group("desc")
    return "", None, first_line


def generate_changelog(
    commits: list[tuple[str, str]],
    version: str,
    previous_version: str | None = None,
) -> str:
    """Generate a markdown changelog from a list of (hash, message) tuples.

    Args:
        commits: List of (commit_hash, full_message) tuples.
        version: The new version being released.
        previous_version: The previous version (for the header).

    Returns:
        Markdown-formatted changelog string.
    """
    sections: dict[str, ChangelogSection] = {}

    for commit_hash, message in commits:
        commit_type, scope, desc = parse_commit_message(message)
        section_title = SECTION_MAP.get(commit_type, DEFAULT_SECTION)

        if section_title not in sections:
            sections[section_title] = ChangelogSection(title=section_title)

        sections[section_title].entries.append(
            ChangelogEntry(
                commit_hash=commit_hash[:7],
                message=desc,
                scope=scope,
            )
        )

    # Build markdown
    lines: list[str] = []

    if previous_version:
        lines.append(f"## [{version}] — comparison with {previous_version}")
    else:
        lines.append(f"## [{version}]")

    lines.append("")

    # Emit sections in a stable order
    section_order = [
        "Features", "Bug Fixes", "Performance", "Refactoring",
        "Documentation", "Tests", "CI", "Build", "Chores", "Other Changes",
    ]

    for title in section_order:
        section = sections.get(title)
        if not section or not section.entries:
            continue
        lines.append(f"### {title}")
        lines.append("")
        for entry in section.entries:
            scope_str = f"**{entry.scope}**: " if entry.scope else ""
            lines.append(f"- {scope_str}{entry.message} ({entry.commit_hash})")
        lines.append("")

    return "\n".join(lines)