#!/usr/bin/env python3
"""
Version updater script for LazySSH.

This script is a compatibility wrapper that uses Hatch for version management.
The version is stored in src/lazyssh/__init__.py and read dynamically by Hatch.

Usage:
    python scripts/release.py 1.2.3

Alternatively, use Hatch directly:
    hatch version 1.2.3
"""

import argparse
import re
import subprocess
import sys


def check_hatch_installed() -> bool:
    """Check if Hatch is installed."""
    try:
        subprocess.run(["hatch", "--version"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def get_current_version() -> str:
    """Get current version using Hatch."""
    result = subprocess.run(["hatch", "version"], capture_output=True, text=True, check=True)
    return result.stdout.strip()


def update_version(new_version: str) -> bool:
    """Update version using Hatch."""
    try:
        subprocess.run(["hatch", "version", new_version], check=True)
        return True
    except subprocess.CalledProcessError:
        return False


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Update version using Hatch. Version is stored in src/lazyssh/__init__.py"
    )
    parser.add_argument("version", help="New version number (e.g., 1.1.2)")

    args = parser.parse_args()

    # Check Hatch is installed
    if not check_hatch_installed():
        print("Hatch is not installed. Install with: pipx install hatch")
        sys.exit(1)

    # Validate version format
    if not re.match(r"^\d+\.\d+\.\d+$", args.version):
        print("Error: Version must be in the format X.Y.Z")
        sys.exit(1)

    # Show current version
    current = get_current_version()
    print(f"Current version: {current}")
    print(f"New version: {args.version}")
    print()

    # Update version
    if update_version(args.version):
        print(f"Successfully updated version to {args.version}")
        print()
        print("Next steps:")
        print("1. Review changes: git diff")
        print(f"2. Commit: git commit -am 'Bump version to {args.version}'")
        print(f"3. Tag: git tag -a v{args.version} -m 'Release v{args.version}'")
        print("4. Push: git push && git push --tags")
    else:
        print("Failed to update version")
        sys.exit(1)


if __name__ == "__main__":
    main()
