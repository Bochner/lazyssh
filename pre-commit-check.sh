#!/bin/bash

# Pre-commit check script for LazySSH
# This script runs all the checks from the GitHub Action before committing code
# It creates a temporary virtual environment, installs all dependencies,
# runs all checks, and cleans up the repository

set -e  # Exit on error

echo "🚀 Running pre-commit checks for LazySSH..."

# Check if python3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3 and try again."
    exit 1
fi

# Get the current Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "ℹ️ Current Python version: $PYTHON_VERSION"

# Check if the Python version is at least 3.11
if [ "$(printf '%s\n' "3.11" "$PYTHON_VERSION" | sort -V | head -n1)" != "3.11" ]; then
    echo "❌ Python 3.11 or higher is required. Current version: $PYTHON_VERSION"
    exit 1
fi

# Create a temporary directory for the virtual environment
VENV_DIR=".pre-commit-venv"
echo "📦 Creating virtual environment in $VENV_DIR..."

# Remove existing virtual environment if it exists
if [ -d "$VENV_DIR" ]; then
    echo "🧹 Removing existing virtual environment..."
    rm -rf "$VENV_DIR"
fi

# Create and activate virtual environment
python3 -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate" || { echo "❌ Failed to activate virtual environment"; exit 1; }

# Upgrade pip to latest version
echo "📦 Upgrading pip..."
pip install --upgrade pip

# Install all development dependencies
echo "📦 Installing development dependencies..."
pip install -e ".[dev]" || { echo "❌ Failed to install development dependencies"; exit 1; }
pip install black isort flake8 mypy pytest build wheel twine pyupgrade typing_extensions || { echo "❌ Failed to install test tools"; exit 1; }

# Function to handle errors and cleanup
cleanup_and_exit() {
    echo "🧹 Cleaning up..."
    deactivate || true
    rm -rf "$VENV_DIR"
    exit 1
}

# Set trap to ensure cleanup on error
trap cleanup_and_exit ERR

# Check 1: Python 3.11+ code optimization
echo "🔍 Running Python 3.11 code optimization check with pyupgrade..."
pyupgrade --py311-plus $(find src -name "*.py")
echo "✅ Python 3.11 code optimization check passed"

# Check 2: Black formatting
echo "🔍 Running Black formatting check..."
black --check --line-length 100 --target-version py311 src tests
echo "✅ Black formatting check passed"

# Check 3: isort check
echo "🔍 Running isort check..."
isort --check-only --profile black src tests
echo "✅ isort check passed"

# Check 4: flake8 linting
echo "🔍 Running flake8 linting check..."
flake8 src tests --count --select=E9,F63,F7,F82 --show-source --statistics
flake8 src tests --count --max-complexity=10 --max-line-length=100 --statistics
echo "✅ flake8 linting check passed"

# Check 5: mypy type checking with stricter settings
echo "🔍 Running mypy type checking with Python 3.11 settings..."
mypy --python-version 3.11 --disallow-untyped-defs --disallow-incomplete-defs --ignore-missing-imports src
echo "✅ mypy type checking passed"

# Check 6: pytest
echo "🔍 Running pytest..."
if [ -d "tests" ] && [ "$(find tests -name "test_*.py" | wc -l)" -gt 0 ]; then
    pytest -xvs tests
    echo "✅ pytest passed"
else
    echo "⚠️ No test files found in tests directory."
    echo "Please add tests to ensure code quality."
fi

# Check 7: Build package
echo "🔍 Building package..."
python -m build
echo "✅ Package built successfully"

# Check 8: Verify package with twine
echo "🔍 Verifying package with twine..."
twine check dist/*
echo "✅ Package verification passed"

# Check 9: Verify Python requirement in pyproject.toml and setup.py
echo "🔍 Checking Python version requirements in package files..."
if [ -f "pyproject.toml" ]; then
    PYPROJECT_PYTHON_REQ=$(grep -E "requires-python|python_requires" pyproject.toml)
    echo "ℹ️ pyproject.toml Python requirement: $PYPROJECT_PYTHON_REQ"
    
    if ! grep -q ">=3.11" pyproject.toml; then
        echo "⚠️ Python requirement in pyproject.toml should be >=3.11"
    fi
fi

if [ -f "setup.py" ]; then
    SETUP_PYTHON_REQ=$(grep -E "python_requires" setup.py)
    echo "ℹ️ setup.py Python requirement: $SETUP_PYTHON_REQ"
    
    if ! grep -q ">=3.11" setup.py; then
        echo "⚠️ Python requirement in setup.py should be >=3.11"
    fi
fi

# Check 10: Verify using pathlib instead of os.path
echo "🔍 Checking for os.path usage that should be replaced with pathlib..."
OSPATH_COUNT=$(grep -r "os\.path\." --include="*.py" src | wc -l)
if [ "$OSPATH_COUNT" -gt 0 ]; then
    echo "⚠️ Found $OSPATH_COUNT instances of os.path usage that could be replaced with pathlib:"
    grep -r "os\.path\." --include="*.py" src | head -10
fi

# Deactivate and remove the virtual environment
deactivate || true
echo "🧹 Cleaning up virtual environment..."
rm -rf "$VENV_DIR"

# Clean up Python cache files
echo "🧹 Cleaning up Python cache files..."
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type f -name "*.pyc" -delete
find . -type f -name "*.pyo" -delete
find . -type f -name "*.pyd" -delete
find . -type d -name "*.egg-info" -exec rm -rf {} +
find . -type d -name "*.egg" -exec rm -rf {} +
find . -type d -name ".pytest_cache" -exec rm -rf {} +
find . -type d -name ".mypy_cache" -exec rm -rf {} +
find . -type d -name ".coverage" -exec rm -rf {} +
find . -type d -name "htmlcov" -exec rm -rf {} +
find . -type d -name "dist" -exec rm -rf {} +
find . -type d -name "build" -exec rm -rf {} +

echo "🎉 All checks passed! Repository is clean. You can safely commit your code." 