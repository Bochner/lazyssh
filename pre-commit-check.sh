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
pip install black isort flake8 mypy pytest build wheel twine pyupgrade || { echo "❌ Failed to install test tools"; exit 1; }

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

# Check 5: Python version compatibility
echo "🔍 Running Python version compatibility checks..."

# Create a temporary file for the compatibility report
COMPAT_REPORT="python_compat_issues.txt"
> $COMPAT_REPORT

echo "Checking for Python 3.7+ compatibility issues..." >> $COMPAT_REPORT
echo "-----------------------------------------" >> $COMPAT_REPORT

# Check for Python 3.8+ specific syntax (walrus operator)
echo "1. Checking for walrus operator (:=) usage (Python 3.8+)..." >> $COMPAT_REPORT
grep -r ":=" --include="*.py" src >> $COMPAT_REPORT 2>/dev/null || echo "✅ No walrus operator usage found." >> $COMPAT_REPORT

# Check for Python 3.9+ dictionary union operators
echo "2. Checking for dictionary union operator (|) usage (Python 3.9+)..." >> $COMPAT_REPORT
grep -r " | " --include="*.py" src | grep -E "dict|{" >> $COMPAT_REPORT 2>/dev/null || echo "✅ No dictionary union operator usage found." >> $COMPAT_REPORT

# Check for Python 3.10+ match/case statements
echo "3. Checking for match/case statements (Python 3.10+)..." >> $COMPAT_REPORT
grep -r "match " --include="*.py" src | grep -E "case" >> $COMPAT_REPORT 2>/dev/null || echo "✅ No match/case statements found." >> $COMPAT_REPORT

# Check for Python 3.10+ union operator in type hints
echo "4. Checking for union operator in type hints (Python 3.10+)..." >> $COMPAT_REPORT
grep -r " | " --include="*.py" src | grep -E "def |-> |: " >> $COMPAT_REPORT 2>/dev/null || echo "✅ No union operator in type hints found." >> $COMPAT_REPORT

# Check for usage of typing.Self (Python 3.11+)
echo "5. Checking for Self type annotation usage (Python 3.11+)..." >> $COMPAT_REPORT
grep -r "Self" --include="*.py" src >> $COMPAT_REPORT 2>/dev/null || echo "✅ No Self type annotation usage found." >> $COMPAT_REPORT

# Check for pattern matching (Python 3.10+)
echo "6. Checking for pattern matching (Python 3.10+)..." >> $COMPAT_REPORT
grep -r "match " --include="*.py" src >> $COMPAT_REPORT 2>/dev/null || echo "✅ No pattern matching usage found." >> $COMPAT_REPORT

# Check for other Python 3.9+ specific methods
echo "7. Checking for Python 3.9+ specific methods..." >> $COMPAT_REPORT
grep -r "str\.removeprefix\|str\.removesuffix\|dict\.update()" --include="*.py" src >> $COMPAT_REPORT 2>/dev/null || echo "✅ No Python 3.9+ specific methods found." >> $COMPAT_REPORT

# Run pyupgrade to identify potential Python version compatibility issues
echo "8. Running pyupgrade for Python 3.7 compatibility check..." >> $COMPAT_REPORT
find src -name "*.py" | xargs pyupgrade --py37-plus >> $COMPAT_REPORT 2>&1 || echo "⚠️ pyupgrade found some issues. See report for details." >> $COMPAT_REPORT

# Check if we have Python 3.7 installed and run test with it if available
echo "9. Attempting to test with Python 3.7 if available..." >> $COMPAT_REPORT

if command -v python3.7 &> /dev/null; then
    echo "ℹ️ Python 3.7 found, creating test environment..."
    
    # Create Python 3.7 test environment
    PY37_VENV=".py37-test-venv"
    python3.7 -m venv $PY37_VENV
    source $PY37_VENV/bin/activate
    
    # Install the package
    echo "ℹ️ Installing package in Python 3.7 environment..."
    pip install --upgrade pip
    pip install -e . >> $COMPAT_REPORT 2>&1
    
    # Run simple import test
    echo "ℹ️ Testing imports in Python 3.7 environment..."
    python -c "import lazyssh; print('✅ Successfully imported lazyssh in Python 3.7')" >> $COMPAT_REPORT 2>&1 || echo "❌ Failed to import lazyssh in Python 3.7" >> $COMPAT_REPORT
    
    # Deactivate and cleanup
    deactivate
    rm -rf $PY37_VENV
else
    echo "⚠️ Python 3.7 not found. Skipping direct Python 3.7 compatibility test." >> $COMPAT_REPORT
    echo "   Consider installing Python 3.7 or using a Docker container for testing." >> $COMPAT_REPORT
fi

# Print the compatibility report
echo ""
echo "📋 Python Version Compatibility Report:"
echo "======================================="
cat $COMPAT_REPORT

# Check if there are any issues
if grep -q -E ":|match|walrus" $COMPAT_REPORT && ! grep -q "✅" $COMPAT_REPORT; then
    echo "⚠️ Potential Python 3.7+ compatibility issues found."
    echo "   Please review the report and resolve any issues."
    echo "   You may need to update pyproject.toml to require Python 3.8+ or higher"
    echo "   or update your code to be compatible with Python 3.7+."
else
    echo "✅ No obvious Python 3.7+ compatibility issues found."
fi

# Clean up the report file
rm $COMPAT_REPORT

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
fi

if [ -f "setup.py" ]; then
    SETUP_PYTHON_REQ=$(grep -E "python_requires" setup.py)
    echo "ℹ️ setup.py Python requirement: $SETUP_PYTHON_REQ"
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