"""PyPI publishing via build + twine."""

from __future__ import annotations

import subprocess
import shutil
from pathlib import Path


def publish_pypi(directory: Path | None = None, test: bool = False) -> str:
    """Build and publish a package to PyPI (or TestPyPI).

    Args:
        directory: Project root directory. Defaults to cwd.
        test: If True, publish to TestPyPI instead of PyPI.

    Returns:
        Output message from the publish command.

    Raises:
        RuntimeError: If build or publish fails.
    """
    cwd = str(directory or Path.cwd())

    # Check for build and twine
    if not shutil.which("python"):
        raise RuntimeError("python not found on PATH")
    if not shutil.which("twine"):
        raise RuntimeError("twine not found on PATH. Install with: pip install twine")

    # Clean dist/
    dist_dir = Path(cwd) / "dist"
    if dist_dir.exists():
        shutil.rmtree(dist_dir)

    # Build
    result = subprocess.run(
        ["python", "-m", "build"],
        cwd=cwd,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Build failed:\n{result.stderr}")

    # Publish
    repository_url = None
    if test:
        repository_url = "https://test.pypi.org/legacy/"

    cmd = ["twine", "upload", "dist/*"]
    if repository_url:
        cmd.extend(["--repository-url", repository_url])

    result = subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Upload failed:\n{result.stderr}")

    return result.stdout.strip() or "Package published successfully."