#!/usr/bin/env python3
"""
Version updater script for LazySSH.

This script only updates version numbers in:
1. pyproject.toml
2. src/lazyssh/__init__.py
"""
import argparse
import re
import sys
from pathlib import Path


def get_repo_root():
    """Get the absolute path to the repository root."""
    # Path to this script
    script_path = Path(__file__).resolve()
    # The repository root is the parent directory of the scripts directory
    return script_path.parent.parent


def update_version(new_version):
    """Update version numbers in the two essential files."""
    updated_files = []
    repo_root = get_repo_root()

    # File 1: Update pyproject.toml
    pyproject_path = repo_root / "pyproject.toml"
    if pyproject_path.exists():
        content = pyproject_path.read_text()

        # Use a simpler approach - read the file line by line and only modify the project version line
        lines = content.splitlines()
        in_project_section = False
        version_updated = False

        for i, line in enumerate(lines):
            if line.strip() == "[project]":
                in_project_section = True
            elif line.strip().startswith("[") and line.strip().endswith("]"):
                in_project_section = False

            if in_project_section and line.strip().startswith("version = "):
                current_version_match = re.search(r'version = "([^"]+)"', line)
                if current_version_match and current_version_match.group(1) == new_version:
                    # Version is already correct
                    print(f"ℹ️ No changes needed in pyproject.toml (already version {new_version})")
                    break

                # Version needs to be updated
                lines[i] = f'version = "{new_version}"'
                updated_files.append(str(pyproject_path))
                print(f"✅ Updated version in pyproject.toml to {new_version}")
                version_updated = True
                break

        # Write the updated content back to the file only if needed
        if version_updated:
            pyproject_path.write_text("\n".join(lines))
    else:
        print(f"❌ Error: pyproject.toml not found at {pyproject_path}")
        return False

    # File 2: Update __init__.py
    init_path = repo_root / "src" / "lazyssh" / "__init__.py"
    if init_path.exists():
        content = init_path.read_text()
        updated_content = re.sub(
            r'__version__ = "[^"]+"', f'__version__ = "{new_version}"', content
        )
        if content != updated_content:
            init_path.write_text(updated_content)
            updated_files.append(str(init_path))
            print(f"✅ Updated version in src/lazyssh/__init__.py to {new_version}")
        else:
            print("ℹ️ No changes needed in src/lazyssh/__init__.py")
    else:
        print(f"❌ Error: __init__.py not found at {init_path}")
        return False

    if updated_files:
        print(f"\n🎉 Successfully updated version to {new_version} in {len(updated_files)} files")
        return True
    else:
        print("\nℹ️ No files were updated. Version may already be up to date.")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Update version numbers in pyproject.toml and __init__.py only"
    )
    parser.add_argument("version", help="New version number (e.g., 1.1.2)")

    args = parser.parse_args()

    # Validate version format
    if not re.match(r"^\d+\.\d+\.\d+$", args.version):
        print("❌ Error: Version must be in the format X.Y.Z")
        sys.exit(1)

    # Update version numbers
    success = update_version(args.version)

    print("\nℹ️ Remember to handle git tagging and releases manually")

    if success:
        print("\n📝 Next steps:")
        print(f"1. Commit the changes: git commit -am 'Bump version to {args.version}'")
        print(f"2. Create a tag: git tag -a v{args.version} -m 'Release v{args.version}'")
        print("3. Push the changes: git push && git push --tags")
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
