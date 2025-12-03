#!/usr/bin/env python3
"""
Update version in pyproject.toml from __init__.py

This ensures version is centralized in src/lintune/__init__.py
"""

import re
from pathlib import Path


def get_version_from_init():
    """Read version from __init__.py"""
    init_file = Path(__file__).parent.parent / "src" / "lintune" / "__init__.py"
    content = init_file.read_text()
    match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', content)
    if match:
        return match.group(1)
    raise ValueError("Could not find __version__ in __init__.py")


def update_pyproject_toml(version):
    """Update version in pyproject.toml"""
    pyproject_file = Path(__file__).parent.parent / "pyproject.toml"
    content = pyproject_file.read_text()
    new_content = re.sub(
        r'version\s*=\s*["\'][^"\']+["\']',
        f'version = "{version}"',
        content,
        count=1
    )
    pyproject_file.write_text(new_content)
    print(f"Updated pyproject.toml to version {version}")


def main():
    version = get_version_from_init()
    print(f"Found version: {version}")
    update_pyproject_toml(version)
    print("✓ Version synchronized successfully")


if __name__ == "__main__":
    main()
