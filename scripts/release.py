#!/usr/bin/env python3
"""
Release script for LazySSH.

This script updates version numbers in all necessary files and creates a Git tag.
It automatically finds and updates all version references throughout the codebase.
"""
import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

def find_all_version_files():
    """Find all files that might contain version information."""
    # Known files that definitely need version updates
    core_files = [
        "pyproject.toml",
        "setup.py",
        "src/lazyssh/__init__.py",
    ]
    
    # Find all Python files that might contain version references
    python_files = []
    for root, _, files in os.walk("src"):
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                if file_path not in core_files:
                    python_files.append(file_path)
    
    # Find documentation files that might contain version references
    doc_files = []
    for ext in [".md", ".rst", ".txt"]:
        for root, _, files in os.walk("."):
            if ".git" in root or "venv" in root or "__pycache__" in root:
                continue
            for file in files:
                if file.endswith(ext):
                    file_path = os.path.join(root, file)
                    doc_files.append(file_path)
    
    return core_files, python_files, doc_files

def update_version(new_version):
    """Update version numbers in all necessary files."""
    core_files, python_files, doc_files = find_all_version_files()
    updated_files = []
    
    # Update core files with known version patterns
    for file_path in core_files:
        path = Path(file_path)
        if not path.exists():
            continue
            
        content = path.read_text()
        original_content = content
        
        # Different patterns for different files
        if file_path == "pyproject.toml":
            content = re.sub(
                r'version = "[^"]+"',
                f'version = "{new_version}"',
                content
            )
        elif file_path == "setup.py":
            content = re.sub(
                r'version="[^"]+"',
                f'version="{new_version}"',
                content
            )
        elif file_path == "src/lazyssh/__init__.py":
            content = re.sub(
                r'__version__ = "[^"]+"',
                f'__version__ = "{new_version}"',
                content
            )
        
        if content != original_content:
            path.write_text(content)
            updated_files.append(file_path)
            print(f"Updated version in {file_path}")
    
    # Search for version patterns in Python files
    for file_path in python_files:
        path = Path(file_path)
        content = path.read_text()
        original_content = content
        
        # Common version patterns in Python files
        patterns = [
            (r'VERSION = ["\']([0-9]+\.[0-9]+\.[0-9]+)["\']', f'VERSION = "{new_version}"'),
            (r'version = ["\']([0-9]+\.[0-9]+\.[0-9]+)["\']', f'version = "{new_version}"'),
            (r'__version__ = ["\']([0-9]+\.[0-9]+\.[0-9]+)["\']', f'__version__ = "{new_version}"'),
            (r'version=["\']([0-9]+\.[0-9]+\.[0-9]+)["\']', f'version="{new_version}"'),
        ]
        
        for pattern, replacement in patterns:
            content = re.sub(pattern, replacement, content)
        
        if content != original_content:
            path.write_text(content)
            updated_files.append(file_path)
            print(f"Updated version in {file_path}")
    
    # Search for version patterns in documentation files
    for file_path in doc_files:
        path = Path(file_path)
        content = path.read_text()
        original_content = content
        
        # Look for version badges, headers, or specific version mentions
        # Be careful with documentation to avoid false positives
        patterns = [
            (r'lazyssh v[0-9]+\.[0-9]+\.[0-9]+', f'lazyssh v{new_version}'),
            (r'LazySSH v[0-9]+\.[0-9]+\.[0-9]+', f'LazySSH v{new_version}'),
            (r'version: [0-9]+\.[0-9]+\.[0-9]+', f'version: {new_version}'),
            (r'Version: [0-9]+\.[0-9]+\.[0-9]+', f'Version: {new_version}'),
            (r'VERSION: [0-9]+\.[0-9]+\.[0-9]+', f'VERSION: {new_version}'),
        ]
        
        for pattern, replacement in patterns:
            content = re.sub(pattern, replacement, content)
        
        if content != original_content:
            path.write_text(content)
            updated_files.append(file_path)
            print(f"Updated version in {file_path}")
    
    return updated_files

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
    parser.add_argument("--dry-run", action="store_true", help="Show what would be updated without making changes")
    
    args = parser.parse_args()
    
    # Validate version format
    if not re.match(r"^\d+\.\d+\.\d+$", args.version):
        print("Error: Version must be in the format X.Y.Z")
        sys.exit(1)
    
    # Update version numbers
    if args.dry_run:
        print(f"Dry run: Would update version to {args.version}")
        core_files, python_files, doc_files = find_all_version_files()
        print(f"Would check {len(core_files)} core files, {len(python_files)} Python files, and {len(doc_files)} documentation files")
    else:
        updated_files = update_version(args.version)
        print(f"\nUpdated version to {args.version} in {len(updated_files)} files")
    
    # Create Git tag
    if not args.no_tag and not args.dry_run:
        create_git_tag(args.version)
    
    if not args.dry_run:
        print("\nNext steps:")
        print(f"1. Commit the changes: git commit -am 'Bump version to {args.version}'")
        print("2. Push the changes: git push")
        print(f"3. Push the tag: git push origin v{args.version}")
        print("4. Create a release on GitHub")

if __name__ == "__main__":
    main() 