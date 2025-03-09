#!/usr/bin/env python3
"""
Release script for LazySSH.

This script updates version numbers in all necessary files and creates a Git tag.
"""
import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

# Files that need version updates
VERSION_FILES = [
    "pyproject.toml",
    "setup.py",
    "src/lazyssh/__init__.py",
]

def update_version(new_version):
    """Update version numbers in all necessary files."""
    # Update pyproject.toml
    pyproject_path = Path("pyproject.toml")
    if pyproject_path.exists():
        content = pyproject_path.read_text()
        content = re.sub(
            r'version = "[^"]+"',
            f'version = "{new_version}"',
            content
        )
        pyproject_path.write_text(content)
        print(f"Updated version in {pyproject_path}")

    # Update setup.py
    setup_path = Path("setup.py")
    if setup_path.exists():
        content = setup_path.read_text()
        content = re.sub(
            r'version="[^"]+"',
            f'version="{new_version}"',
            content
        )
        setup_path.write_text(content)
        print(f"Updated version in {setup_path}")

    # Update __init__.py
    init_path = Path("src/lazyssh/__init__.py")
    if init_path.exists():
        content = init_path.read_text()
        content = re.sub(
            r'__version__ = "[^"]+"',
            f'__version__ = "{new_version}"',
            content
        )
        init_path.write_text(content)
        print(f"Updated version in {init_path}")

def create_git_tag(version):
    """Create a Git tag for the new version."""
    tag_name = f"v{version}"
    
    # Check if tag already exists
    result = subprocess.run(
        ["git", "tag", "-l", tag_name],
        capture_output=True,
        text=True,
    )
    
    if tag_name in result.stdout:
        print(f"Tag {tag_name} already exists!")
        return False
    
    # Create tag
    subprocess.run(["git", "tag", "-a", tag_name, "-m", f"Release {tag_name}"])
    print(f"Created Git tag {tag_name}")
    
    return True

def main():
    parser = argparse.ArgumentParser(description="Release a new version of LazySSH")
    parser.add_argument("version", help="New version number (e.g., 1.0.1)")
    parser.add_argument("--no-tag", action="store_true", help="Don't create a Git tag")
    
    args = parser.parse_args()
    
    # Validate version format
    if not re.match(r"^\d+\.\d+\.\d+$", args.version):
        print("Error: Version must be in the format X.Y.Z")
        sys.exit(1)
    
    # Update version numbers
    update_version(args.version)
    
    # Create Git tag
    if not args.no_tag:
        create_git_tag(args.version)
    
    print(f"\nVersion updated to {args.version}")
    print("\nNext steps:")
    print("1. Commit the changes: git commit -am 'Bump version to {args.version}'")
    print("2. Push the changes: git push")
    print("3. Push the tag: git push origin v{args.version}")
    print("4. Create a release on GitHub")

if __name__ == "__main__":
    main() 