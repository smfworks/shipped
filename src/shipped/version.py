"""Version parsing and bumping.

Supports SemVer (MAJOR.MINOR.PATCH) with optional pre-release labels.
Reads and writes version from pyproject.toml [project] version field.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib  # type: ignore[no-redef]

import tomli_w


SEMVER_RE = re.compile(
    r"^(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)\.(?P<patch>0|[1-9]\d*)"
    r"(?:-(?P<pre>[a-zA-Z0-9.]+))?$"
)


@dataclass(frozen=True)
class Version:
    major: int
    minor: int
    patch: int
    pre: str | None = None

    def __str__(self) -> str:
        base = f"{self.major}.{self.minor}.{self.patch}"
        if self.pre:
            return f"{base}-{self.pre}"
        return base

    @classmethod
    def parse(cls, version_str: str) -> Version:
        """Parse a SemVer string into a Version."""
        m = SEMVER_RE.match(version_str.strip())
        if not m:
            raise ValueError(f"Invalid SemVer string: {version_str!r}")
        pre = m.group("pre")
        return cls(
            major=int(m.group("major")),
            minor=int(m.group("minor")),
            patch=int(m.group("patch")),
            pre=pre,
        )


def bump_version(current: Version, part: str) -> Version:
    """Bump a version by the given part: major, minor, or patch.

    - major: resets minor and patch to 0
    - minor: resets patch to 0
    - patch: increments patch
    Drops any pre-release label on bump.
    """
    if part == "major":
        return Version(major=current.major + 1, minor=0, patch=0)
    elif part == "minor":
        return Version(major=current.major, minor=current.minor + 1, patch=0)
    elif part == "patch":
        return Version(major=current.major, minor=current.minor, patch=current.patch + 1)
    else:
        raise ValueError(f"Invalid bump part: {part!r}. Use 'major', 'minor', or 'patch'.")


def read_version_from_pyproject(path: Path | None = None) -> Version:
    """Read the current version from pyproject.toml."""
    if path is None:
        path = Path("pyproject.toml")
    if not path.exists():
        raise FileNotFoundError(f"pyproject.toml not found at {path}")
    with open(path, "rb") as f:
        data = tomllib.load(f)
    version_str = data.get("project", {}).get("version", "")
    if not version_str:
        raise ValueError("No [project] version found in pyproject.toml")
    return Version.parse(version_str)


def write_version_to_pyproject(version: Version, path: Path | None = None) -> None:
    """Write the new version back to pyproject.toml, preserving all other content."""
    if path is None:
        path = Path("pyproject.toml")
    with open(path, "rb") as f:
        data = tomllib.load(f)
    data.setdefault("project", {})["version"] = str(version)
    with open(path, "wb") as f:
        tomli_w.dump(data, f)