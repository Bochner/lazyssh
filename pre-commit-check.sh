#!/bin/bash

# Pre-commit check script for LazySSH (Enhanced Edition)
# This script runs comprehensive checks and attempts to auto-fix issues where possible.
# It creates a temporary virtual environment, installs all dependencies,
# runs all checks with auto-fix, and reports results with actionable feedback.

set -e  # Exit on error
set -o pipefail  # Ensure pipeline failures are caught

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Track fixes and errors
FIXES_APPLIED=0
ERRORS_FOUND=0
WARNINGS_FOUND=0

# Mode flags
AUTO_FIX=1  # Default to auto-fix mode
DRY_RUN=0
SKIP_TESTS=0
SKIP_BUILD=0
VERBOSE=0

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --no-fix)
            AUTO_FIX=0
            shift
            ;;
        --dry-run)
            DRY_RUN=1
            AUTO_FIX=0
            shift
            ;;
        --skip-tests)
            SKIP_TESTS=1
            shift
            ;;
        --skip-build)
            SKIP_BUILD=1
            shift
            ;;
        --verbose|-v)
            VERBOSE=1
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [options]"
            echo ""
            echo "Options:"
            echo "  --no-fix       Check only, don't auto-fix issues"
            echo "  --dry-run      Show what would be fixed without making changes"
            echo "  --skip-tests   Skip running tests"
            echo "  --skip-build   Skip building the package"
            echo "  --verbose, -v  Show detailed output"
            echo "  --help, -h     Show this help message"
            echo ""
            echo "Default behavior: Auto-fix mode (attempts to fix issues)"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

echo -e "${BOLD}${BLUE}🚀 LazySSH Pre-Commit Checks${NC}"
echo -e "${CYAN}=================================${NC}"
echo ""

if [ $AUTO_FIX -eq 1 ]; then
    echo -e "${GREEN}Mode: Auto-fix (will attempt to fix issues)${NC}"
elif [ $DRY_RUN -eq 1 ]; then
    echo -e "${YELLOW}Mode: Dry-run (showing what would be fixed)${NC}"
else
    echo -e "${YELLOW}Mode: Check-only (no auto-fix)${NC}"
fi
echo ""

# Function to print section header
print_section() {
    echo ""
    echo -e "${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BOLD}${BLUE}$1${NC}"
    echo -e "${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

# Function to print success
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

# Function to print error
print_error() {
    echo -e "${RED}✗ $1${NC}"
    ERRORS_FOUND=$((ERRORS_FOUND + 1))
}

# Function to print warning
print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
    WARNINGS_FOUND=$((WARNINGS_FOUND + 1))
}

# Function to print info
print_info() {
    echo -e "${CYAN}→ $1${NC}"
}

# Function to print fix applied
print_fix() {
    echo -e "${GREEN}🔧 Fixed: $1${NC}"
    FIXES_APPLIED=$((FIXES_APPLIED + 1))
}

# Check if python3 is available
print_section "System Requirements Check"

if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed. Please install Python 3 and try again."
    exit 1
fi

# Get the current Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
print_info "Python version: $PYTHON_VERSION"

# Check if the Python version is at least 3.11
if [ "$(printf '%s\n' "3.11" "$PYTHON_VERSION" | sort -V | head -n1)" != "3.11" ]; then
    print_error "Python 3.11 or higher is required. Current version: $PYTHON_VERSION"
    exit 1
fi

print_success "Python 3.11+ detected"

# Create a temporary directory for the virtual environment
VENV_DIR=".pre-commit-venv"
print_section "Environment Setup"

# Remove existing virtual environment if it exists
if [ -d "$VENV_DIR" ]; then
    print_info "Removing existing virtual environment..."
    rm -rf "$VENV_DIR"
fi

print_info "Creating virtual environment in $VENV_DIR..."
python3 -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate" || { print_error "Failed to activate virtual environment"; exit 1; }

# Upgrade pip to latest version
print_info "Upgrading pip..."
pip install --upgrade pip > /dev/null 2>&1

# Install all development dependencies
print_info "Installing development dependencies..."
pip install -e ".[dev]" > /dev/null 2>&1 || { print_error "Failed to install development dependencies"; exit 1; }
pip install pyupgrade typing_extensions > /dev/null 2>&1 || { print_error "Failed to install additional tools"; exit 1; }

# Verify flake8 is installed and available
which flake8 > /dev/null 2>&1 || { print_error "flake8 not found in PATH after installation"; exit 1; }

print_success "Environment setup complete"

# Function to handle errors and cleanup
cleanup_and_exit() {
    local exit_code=$1
    print_section "Cleanup"
    print_info "Deactivating virtual environment..."
    deactivate 2>/dev/null || true
    print_info "Removing virtual environment..."
    rm -rf "$VENV_DIR"
    
    # Clean up Python cache files
    print_info "Cleaning up Python cache files..."
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete 2>/dev/null || true
    find . -type f -name "*.pyo" -delete 2>/dev/null || true
    find . -type f -name "*.pyd" -delete 2>/dev/null || true
    find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
    find . -type d -name "*.egg" -exec rm -rf {} + 2>/dev/null || true
    find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
    find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name ".coverage" -exec rm -f {} + 2>/dev/null || true
    find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
    find . -type d -name "dist" -exec rm -rf {} + 2>/dev/null || true
    find . -type d -name "build" -exec rm -rf {} + 2>/dev/null || true
    
    print_success "Cleanup complete"
    exit "$exit_code"
}

# Set trap to ensure cleanup on error
trap 'cleanup_and_exit 1' ERR INT TERM

#============================================================================
# Auto-fix Phase: Fix what can be automatically fixed
#============================================================================

if [ $AUTO_FIX -eq 1 ] || [ $DRY_RUN -eq 1 ]; then
    print_section "Auto-Fix Phase"
    
    # Fix 1: Python 3.11+ code optimization with pyupgrade
    print_info "Running pyupgrade for Python 3.11+ optimizations..."
    if [ $DRY_RUN -eq 1 ]; then
        print_info "Dry-run: Would run pyupgrade on all Python files"
    else
        PYUPGRADE_OUTPUT=$(find src -name "*.py" -exec pyupgrade --py311-plus {} \; 2>&1)
        if [ -n "$PYUPGRADE_OUTPUT" ]; then
            print_fix "Applied Python 3.11+ optimizations"
            [ $VERBOSE -eq 1 ] && echo "$PYUPGRADE_OUTPUT"
        else
            print_success "Code already optimized for Python 3.11+"
        fi
    fi
    
    # Fix 2: Auto-format imports with isort
    print_info "Auto-formatting imports with isort..."
    if [ $DRY_RUN -eq 1 ]; then
        ISORT_CHECK=$(isort --check-only --profile black src tests 2>&1 || true)
        if [ -n "$ISORT_CHECK" ]; then
            print_info "Dry-run: Would fix import ordering"
            [ $VERBOSE -eq 1 ] && echo "$ISORT_CHECK"
        else
            print_success "Import ordering already correct"
        fi
    else
        ISORT_OUTPUT=$(isort --profile black src tests 2>&1)
        if echo "$ISORT_OUTPUT" | grep -q "Fixing"; then
            print_fix "Fixed import ordering"
            [ $VERBOSE -eq 1 ] && echo "$ISORT_OUTPUT"
        else
            print_success "Import ordering already correct"
        fi
    fi
    
    # Fix 3: Auto-format code with Black
    print_info "Auto-formatting code with Black..."
    if [ $DRY_RUN -eq 1 ]; then
        BLACK_CHECK=$(black --check --line-length 100 --target-version py311 src tests 2>&1 || true)
        if echo "$BLACK_CHECK" | grep -q "would be reformatted"; then
            print_info "Dry-run: Would reformat code with Black"
            [ $VERBOSE -eq 1 ] && echo "$BLACK_CHECK"
        else
            print_success "Code formatting already correct"
        fi
    else
        BLACK_OUTPUT=$(black --line-length 100 --target-version py311 src tests 2>&1)
        if echo "$BLACK_OUTPUT" | grep -q "reformatted"; then
            print_fix "Reformatted code with Black"
            [ $VERBOSE -eq 1 ] && echo "$BLACK_OUTPUT"
        else
            print_success "Code formatting already correct"
        fi
    fi
    
    if [ $DRY_RUN -eq 0 ] && [ $FIXES_APPLIED -gt 0 ]; then
        echo ""
        print_success "Applied $FIXES_APPLIED automatic fixes"
    fi
fi

#============================================================================
# Verification Phase: Check for remaining issues
#============================================================================

print_section "Code Quality Checks"

# Check 1: Verify Black formatting
print_info "Verifying Black formatting..."
if black --check --line-length 100 --target-version py311 src tests 2>&1 | tee /tmp/black_check.log; then
    print_success "Black formatting check passed"
else
    print_error "Black formatting issues detected"
    if [ $AUTO_FIX -eq 0 ]; then
        print_info "Run with auto-fix mode or execute: black --line-length 100 --target-version py311 src tests"
    fi
    cat /tmp/black_check.log
fi
rm -f /tmp/black_check.log

# Check 2: Verify isort
print_info "Verifying isort..."
if isort --check-only --profile black src tests 2>&1 | tee /tmp/isort_check.log; then
    print_success "isort check passed"
else
    print_error "isort issues detected"
    if [ $AUTO_FIX -eq 0 ]; then
        print_info "Run with auto-fix mode or execute: isort --profile black src tests"
    fi
    cat /tmp/isort_check.log
fi
rm -f /tmp/isort_check.log

# Check 3: flake8 linting (critical errors)
print_info "Running flake8 linting (critical errors)..."
if flake8 src tests --count --select=E9,F63,F7,F82 --show-source --statistics 2>&1; then
    print_success "No critical flake8 errors found"
else
    print_error "Critical flake8 errors detected (require manual fix)"
fi

# Check 4: flake8 linting (full check)
print_info "Running flake8 linting (full check)..."
if flake8 src tests --count --max-complexity=10 --max-line-length=100 --statistics 2>&1; then
    print_success "flake8 full check passed"
else
    print_error "flake8 issues detected (may require manual fix)"
fi

# Check 5: mypy type checking
print_section "Type Checking"
print_info "Running mypy type checking..."
if mypy --python-version 3.11 --disallow-untyped-defs --disallow-incomplete-defs --ignore-missing-imports src 2>&1 | tee /tmp/mypy_check.log; then
    print_success "mypy type checking passed"
else
    print_error "Type checking issues detected (require manual fix)"
    cat /tmp/mypy_check.log
fi
rm -f /tmp/mypy_check.log

#============================================================================
# Testing Phase
#============================================================================

if [ $SKIP_TESTS -eq 0 ]; then
    print_section "Testing"
    
    print_info "Running pytest..."
    if [ -d "tests" ] && [ "$(find tests -name "test_*.py" | wc -l || echo 0)" -gt 0 ]; then
        if pytest -xvs tests 2>&1 | tee /tmp/pytest.log; then
            print_success "All tests passed"
        else
            print_error "Tests failed (require manual fix)"
            cat /tmp/pytest.log
        fi
        rm -f /tmp/pytest.log
    else
        print_warning "No test files found in tests directory"
    fi
else
    print_info "Skipping tests (--skip-tests flag)"
fi

#============================================================================
# Build Verification
#============================================================================

if [ $SKIP_BUILD -eq 0 ]; then
    print_section "Build Verification"
    
    # Check 1: Build package
    print_info "Building package..."
    if python -m build 2>&1 | tee /tmp/build.log; then
        print_success "Package built successfully"
    else
        print_error "Package build failed"
        cat /tmp/build.log
    fi
    rm -f /tmp/build.log
    
    # Check 2: Verify package with twine
    print_info "Verifying package with twine..."
    if twine check dist/* 2>&1 | tee /tmp/twine.log; then
        print_success "Package verification passed"
    else
        print_error "Package verification failed"
        cat /tmp/twine.log
    fi
    rm -f /tmp/twine.log
else
    print_info "Skipping build verification (--skip-build flag)"
fi

#============================================================================
# Additional Checks
#============================================================================

print_section "Additional Checks"

# Check: Python version requirement in pyproject.toml
print_info "Checking Python version requirement in pyproject.toml..."
if [ -f "pyproject.toml" ]; then
    PYPROJECT_PYTHON_REQ=$(grep -E "requires-python|python_requires" pyproject.toml || true)
    [ $VERBOSE -eq 1 ] && echo "  $PYPROJECT_PYTHON_REQ"
    
    if ! grep -q ">=3.11" pyproject.toml; then
        print_warning "Python requirement in pyproject.toml should be >=3.11"
    else
        print_success "Python version requirement is correct (>=3.11)"
    fi
fi

# Check: Verify using pathlib instead of os.path
print_info "Checking for os.path usage (should use pathlib)..."
OSPATH_COUNT=$(grep -r "os\.path\." --include="*.py" src 2>/dev/null | wc -l | tr -d ' ' || true)
if [ "$OSPATH_COUNT" -gt 0 ]; then
    print_warning "Found $OSPATH_COUNT instances of os.path usage (consider using pathlib)"
    if [ $VERBOSE -eq 1 ]; then
        grep -r "os\.path\." --include="*.py" src | head -10 || true
    fi
else
    print_success "No os.path usage found (using pathlib)"
fi

# Check: Version consistency
print_info "Checking version consistency..."
PYPROJECT_VERSION=$(grep -m 1 'version = ' pyproject.toml | cut -d '"' -f 2 || true)
INIT_VERSION=$(grep '__version__' src/lazyssh/__init__.py | cut -d '"' -f 2 || true)

if [ "$PYPROJECT_VERSION" = "$INIT_VERSION" ]; then
    print_success "Version is consistent across files: $PYPROJECT_VERSION"
else
    print_error "Version mismatch: pyproject.toml($PYPROJECT_VERSION) != __init__.py($INIT_VERSION)"
fi

#============================================================================
# Summary Report
#============================================================================

print_section "Summary Report"

echo ""
if [ $FIXES_APPLIED -gt 0 ]; then
    echo -e "${GREEN}${BOLD}✓ Fixes Applied: $FIXES_APPLIED${NC}"
fi

if [ $ERRORS_FOUND -eq 0 ] && [ $WARNINGS_FOUND -eq 0 ]; then
    echo -e "${GREEN}${BOLD}✓✓✓ All Checks Passed! ✓✓✓${NC}"
    echo -e "${GREEN}Repository is clean and ready for commit${NC}"
    FINAL_EXIT_CODE=0
elif [ $ERRORS_FOUND -eq 0 ]; then
    echo -e "${YELLOW}${BOLD}⚠ Warnings Found: $WARNINGS_FOUND${NC}"
    echo -e "${YELLOW}No critical errors, but please review warnings${NC}"
    FINAL_EXIT_CODE=0
else
    echo -e "${RED}${BOLD}✗ Errors Found: $ERRORS_FOUND${NC}"
    if [ $WARNINGS_FOUND -gt 0 ]; then
        echo -e "${YELLOW}${BOLD}⚠ Warnings Found: $WARNINGS_FOUND${NC}"
    fi
    echo ""
    echo -e "${RED}${BOLD}Repository has issues that need attention${NC}"
    echo ""
    echo -e "${CYAN}Suggested actions:${NC}"
    if [ $AUTO_FIX -eq 0 ]; then
        echo -e "${CYAN}  1. Run this script without --no-fix to auto-fix formatting issues${NC}"
    fi
    echo -e "${CYAN}  2. Review and fix type checking errors manually${NC}"
	echo -e "${CYAN}  3. Fix any test failures${NC}"
	FINAL_EXIT_CODE=1
fi

echo ""
if [ $DRY_RUN -eq 1 ]; then
    echo -e "${YELLOW}This was a dry-run. No changes were made.${NC}"
    echo -e "${CYAN}Run without --dry-run to apply fixes.${NC}"
fi

# Cleanup and exit
cleanup_and_exit $FINAL_EXIT_CODE
