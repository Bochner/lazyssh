#!/bin/bash

# Pre-commit check script for LazySSH
# This script runs all the checks from the GitHub Action before committing code
# It creates a temporary virtual environment, installs all dependencies,
# runs all checks, and cleans up the repository

set -e  # Exit on error

echo "🚀 Running pre-commit checks for LazySSH..."

# Create a temporary directory for the virtual environment
VENV_DIR=".pre-commit-venv"
echo "📦 Creating virtual environment in $VENV_DIR..."

# Check if python3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3 and try again."
    exit 1
fi

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
pip install black isort flake8 mypy pytest || { echo "❌ Failed to install test tools"; exit 1; }

# Function to handle errors and cleanup
cleanup_and_exit() {
    echo "🧹 Cleaning up..."
    deactivate || true
    rm -rf "$VENV_DIR"
    exit 1
}

# Set trap to ensure cleanup on error
trap cleanup_and_exit ERR

# Check 1: Black formatting
echo "🔍 Running Black formatting check..."
black --check src tests
echo "✅ Black formatting check passed"

# Check 2: isort check
echo "🔍 Running isort check..."
isort --check-only --profile black src tests
echo "✅ isort check passed"

# Check 3: flake8 linting
echo "🔍 Running flake8 linting check..."
flake8 src tests
echo "✅ flake8 linting check passed"

# Check 4: mypy type checking
echo "🔍 Running mypy type checking..."
mypy --ignore-missing-imports src
echo "✅ mypy type checking passed"

# Check 5: pytest
echo "🔍 Running pytest..."
if [ -d "tests" ] && [ "$(find tests -name "test_*.py" | wc -l)" -gt 0 ]; then
    pytest -xvs tests
    echo "✅ pytest passed"
else
    echo "⚠️ No test files found in tests directory."
    echo "Please add tests to ensure code quality."
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