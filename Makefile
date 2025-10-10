.PHONY: help clean install dev-install test coverage fmt fix lint check verify \
        security docs build dist release publish publish-test pre-commit watch \
        version deps-check deps-update all venv-info

# Project settings
PACKAGE_NAME = lazyssh
PYTHON = python3
PIP = pip3
VENV_DIR = venv
VENV_BIN = $(VENV_DIR)/bin
VENV_PYTHON = $(VENV_BIN)/python
VENV_PIP = $(VENV_BIN)/pip
SRC_DIR = src
TEST_DIR = tests
DOCS_DIR = docs

# Tools
BLACK = black
ISORT = isort
PYLINT = pylint
FLAKE8 = flake8
MYPY = mypy
PYTEST = pytest
TWINE = twine
PYUPGRADE = pyupgrade

# Options
BLACK_OPTS = --line-length 100 --target-version py311
ISORT_OPTS = --profile black --line-length 100
PYTEST_OPTS = -xvs
COVERAGE_OPTS = --cov=$(SRC_DIR) --cov-report=html --cov-report=term --cov-report=xml

# Colors for output
RED = \033[0;31m
GREEN = \033[0;32m
YELLOW = \033[1;33m
BLUE = \033[0;34m
NC = \033[0m # No Color

#============================================================================
# Help and Information
#============================================================================

help:
	@echo "$(BLUE)LazySSH Development Makefile$(NC)"
	@echo "=============================="
	@echo ""
	@echo "$(YELLOW)Note: After 'make install' or 'make dev-install', run: source venv/bin/activate$(NC)"
	@echo ""
	@echo "$(GREEN)Setup Commands:$(NC)"
	@echo "  make install          Create venv and install package in editable mode"
	@echo "  make dev-install      Install with all development dependencies"
	@echo "  make venv-info        Show virtual environment information"
	@echo "  make deps-check       Check for outdated dependencies"
	@echo "  make deps-update      Update dependencies to latest versions"
	@echo ""
	@echo "$(GREEN)Code Quality Commands:$(NC)"
	@echo "  make fmt              Format code with Black and isort (view changes)"
	@echo "  make fix              Auto-fix code issues (format + pyupgrade)"
	@echo "  make lint             Run all linting checks (flake8 + pylint)"
	@echo "  make check            Run all quality checks (format, lint, type)"
	@echo "  make verify           Full verification: format, lint, type, tests, build (PyPI-ready)"
	@echo "  make pre-commit       Run pre-commit checks (same as verify)"
	@echo ""
	@echo "$(GREEN)Testing Commands:$(NC)"
	@echo "  make test             Run tests"
	@echo "  make coverage         Run tests with coverage report"
	@echo "  make watch            Run tests in watch mode (requires pytest-watch)"
	@echo ""
	@echo "$(GREEN)Build & Release Commands:$(NC)"
	@echo "  make build            Build the package"
	@echo "  make dist             Build distribution packages (same as build)"
	@echo "  make clean            Clean up build artifacts"
	@echo "  make version          Display current version"
	@echo "  make release          Interactive release process (version bump)"
	@echo "  make publish-test     Publish to TestPyPI"
	@echo "  make publish          Publish to PyPI"
	@echo ""
	@echo "$(GREEN)Documentation Commands:$(NC)"
	@echo "  make docs             Verify documentation files exist"
	@echo ""
	@echo "$(GREEN)Composite Commands:$(NC)"
	@echo "  make all              Run all checks and tests (verify + coverage)"
	@echo ""
	@echo "$(YELLOW)Tip: Run 'make fix' before 'make check' to auto-fix most issues$(NC)"

#============================================================================
# Setup and Dependencies
#============================================================================

install:
	@echo "$(BLUE)Setting up development environment for $(PACKAGE_NAME)...$(NC)"
	@if [ ! -d "$(VENV_DIR)" ]; then \
		echo "$(YELLOW)Creating virtual environment in $(VENV_DIR)/...$(NC)"; \
		$(PYTHON) -m venv $(VENV_DIR); \
		echo "$(GREEN)✓ Virtual environment created$(NC)"; \
	else \
		echo "$(GREEN)✓ Virtual environment already exists$(NC)"; \
	fi
	@echo "$(YELLOW)Installing package in editable mode...$(NC)"
	@$(VENV_PIP) install --upgrade pip setuptools wheel
	@$(VENV_PIP) install -e .
	@echo "$(GREEN)✓ Installation complete!$(NC)"
	@echo ""
	@echo "$(BLUE)To activate the virtual environment, run:$(NC)"
	@echo "  $(YELLOW)source $(VENV_DIR)/bin/activate$(NC)"

dev-install: install
	@echo "$(BLUE)Installing development dependencies...$(NC)"
	@$(VENV_PIP) install -e ".[dev]"
	@$(VENV_PIP) install pyupgrade typing_extensions pytest-watch
	@echo "$(GREEN)✓ Development installation complete!$(NC)"
	@echo ""
	@echo "$(BLUE)To activate the virtual environment, run:$(NC)"
	@echo "  $(YELLOW)source $(VENV_DIR)/bin/activate$(NC)"

deps-check:
	@echo "$(BLUE)Checking for outdated dependencies...$(NC)"
	@if [ -d "$(VENV_DIR)" ]; then \
		$(VENV_PIP) list --outdated; \
	else \
		echo "$(YELLOW)⚠ Virtual environment not found. Run 'make install' first.$(NC)"; \
		exit 1; \
	fi
	@echo "$(GREEN)✓ Dependency check complete$(NC)"

deps-update:
	@if [ ! -d "$(VENV_DIR)" ]; then \
		echo "$(YELLOW)⚠ Virtual environment not found. Run 'make install' first.$(NC)"; \
		exit 1; \
	fi
	@echo "$(YELLOW)⚠ This will update all dependencies. Consider reviewing changes.$(NC)"
	@read -p "Continue? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		$(VENV_PIP) install --upgrade -e ".[dev]"; \
		echo "$(GREEN)✓ Dependencies updated$(NC)"; \
	else \
		echo "$(YELLOW)Update cancelled$(NC)"; \
	fi

venv-info:
	@if [ -d "$(VENV_DIR)" ]; then \
		echo "$(GREEN)✓ Virtual environment exists at: $(VENV_DIR)/$(NC)"; \
		echo "$(BLUE)To activate it, run:$(NC)"; \
		echo "  $(YELLOW)source $(VENV_DIR)/bin/activate$(NC)"; \
		echo ""; \
		echo "$(BLUE)Installed packages:$(NC)"; \
		$(VENV_PIP) list --format=columns 2>/dev/null | head -20 || true; \
	else \
		echo "$(YELLOW)⚠ Virtual environment not found$(NC)"; \
		echo "$(BLUE)Create it with:$(NC)"; \
		echo "  $(YELLOW)make install$(NC)"; \
	fi

#============================================================================
# Code Formatting and Auto-fixing
#============================================================================

fmt:
	@echo "$(BLUE)Formatting code with Black and isort...$(NC)"
	@echo "$(YELLOW)→ Running isort...$(NC)"
	$(ISORT) $(ISORT_OPTS) $(SRC_DIR) $(TEST_DIR)
	@echo "$(YELLOW)→ Running Black...$(NC)"
	$(BLACK) $(BLACK_OPTS) $(SRC_DIR) $(TEST_DIR)
	@echo "$(GREEN)✓ Code formatting complete$(NC)"

fix: fmt
	@echo "$(BLUE)Auto-fixing code issues...$(NC)"
	@echo "$(YELLOW)→ Running pyupgrade for Python 3.11+...$(NC)"
	@find $(SRC_DIR) -name "*.py" -exec $(PYUPGRADE) --py311-plus {} \; 2>/dev/null || true
	@find $(TEST_DIR) -name "*.py" -exec $(PYUPGRADE) --py311-plus {} \; 2>/dev/null || true
	@echo "$(YELLOW)→ Re-running formatters after pyupgrade...$(NC)"
	$(ISORT) $(ISORT_OPTS) $(SRC_DIR) $(TEST_DIR)
	$(BLACK) $(BLACK_OPTS) $(SRC_DIR) $(TEST_DIR)
	@echo "$(GREEN)✓ Auto-fix complete$(NC)"
	@echo "$(YELLOW)→ Run 'make check' to verify all issues are resolved$(NC)"

#============================================================================
# Linting and Type Checking
#============================================================================

lint:
	@echo "$(BLUE)Running linting checks...$(NC)"
	@echo "$(YELLOW)→ Running flake8 (syntax errors)...$(NC)"
	@$(FLAKE8) $(SRC_DIR) $(TEST_DIR) --count --select=E9,F63,F7,F82 --show-source --statistics || \
		(echo "$(RED)✗ Flake8 found critical errors$(NC)" && exit 1)
	@echo "$(YELLOW)→ Running flake8 (full check)...$(NC)"
	@$(FLAKE8) $(SRC_DIR) $(TEST_DIR) --count --max-complexity=10 --max-line-length=100 --statistics || \
		(echo "$(RED)✗ Flake8 found issues$(NC)" && exit 1)
	@echo "$(YELLOW)→ Running pylint...$(NC)"
	@$(PYLINT) $(SRC_DIR) --rcfile=.flake8 2>/dev/null || \
		(echo "$(YELLOW)⚠ Pylint found issues (non-blocking)$(NC)")
	@echo "$(GREEN)✓ Linting complete$(NC)"

typecheck:
	@echo "$(BLUE)Running type checking with mypy...$(NC)"
	@$(MYPY) --python-version 3.11 --disallow-untyped-defs --disallow-incomplete-defs \
		--ignore-missing-imports $(SRC_DIR) || \
		(echo "$(RED)✗ Type checking failed$(NC)" && exit 1)
	@echo "$(GREEN)✓ Type checking complete$(NC)"

#============================================================================
# Comprehensive Checking
#============================================================================

check: 
	@echo "$(BLUE)Running comprehensive code quality checks...$(NC)"
	@echo ""
	@echo "$(BLUE)=== Step 1/5: Format Check ===$(NC)"
	@$(BLACK) --check $(BLACK_OPTS) $(SRC_DIR) $(TEST_DIR) || \
		(echo "$(RED)✗ Black formatting check failed. Run 'make fix' to auto-fix$(NC)" && exit 1)
	@$(ISORT) --check-only $(ISORT_OPTS) $(SRC_DIR) $(TEST_DIR) || \
		(echo "$(RED)✗ isort check failed. Run 'make fix' to auto-fix$(NC)" && exit 1)
	@echo "$(GREEN)✓ Format check passed$(NC)"
	@echo ""
	@echo "$(BLUE)=== Step 2/5: Linting ===$(NC)"
	@$(MAKE) lint
	@echo ""
	@echo "$(BLUE)=== Step 3/5: Type Checking ===$(NC)"
	@$(MAKE) typecheck
	@echo ""
	@echo "$(BLUE)=== Step 4/5: Import Test ===$(NC)"
	@$(PYTHON) -c "import lazyssh; print(f'Successfully imported lazyssh version {lazyssh.__version__}')" || \
		(echo "$(RED)✗ Package import failed$(NC)" && exit 1)
	@echo "$(GREEN)✓ Package import successful$(NC)"
	@echo ""
	@echo "$(BLUE)=== Step 5/5: Pathlib Check ===$(NC)"
	@OSPATH_COUNT=$$(grep -r "os\.path\." --include="*.py" $(SRC_DIR) 2>/dev/null | wc -l | tr -d ' '); \
	if [ "$$OSPATH_COUNT" -gt 0 ]; then \
		echo "$(YELLOW)⚠ Found $$OSPATH_COUNT instances of os.path usage (consider using pathlib)$(NC)"; \
		grep -r "os\.path\." --include="*.py" $(SRC_DIR) | head -5; \
	else \
		echo "$(GREEN)✓ No os.path usage found$(NC)"; \
	fi
	@echo ""
	@echo "$(GREEN)✓ All quality checks passed!$(NC)"

verify:
	@echo "$(BLUE)═══════════════════════════════════════════════════════════════$(NC)"
	@echo "$(BLUE)  COMPREHENSIVE VERIFICATION (PyPI-ready checks)                $(NC)"
	@echo "$(BLUE)═══════════════════════════════════════════════════════════════$(NC)"
	@echo ""
	@if [ ! -f "pre-commit-check.sh" ]; then \
		echo "$(RED)✗ pre-commit-check.sh not found$(NC)"; \
		exit 1; \
	fi
	@chmod +x pre-commit-check.sh
	@bash pre-commit-check.sh --no-fix || exit 1
	@echo ""
	@echo "$(GREEN)═══════════════════════════════════════════════════════════════$(NC)"
	@echo "$(GREEN)  ✓✓✓ ALL VERIFICATION CHECKS PASSED! ✓✓✓                     $(NC)"
	@echo "$(GREEN)  Repository is ready for commit/push/deploy to PyPI           $(NC)"
	@echo "$(GREEN)═══════════════════════════════════════════════════════════════$(NC)"

pre-commit: verify
	@echo "$(GREEN)Pre-commit checks complete$(NC)"

#============================================================================
# Testing
#============================================================================

test:
	@echo "$(BLUE)Running tests...$(NC)"
	@if [ -d "$(TEST_DIR)" ] && [ "$$(find $(TEST_DIR) -name 'test_*.py' | wc -l)" -gt 0 ]; then \
		$(PYTEST) $(PYTEST_OPTS) $(TEST_DIR) || (echo "$(RED)✗ Tests failed$(NC)" && exit 1); \
		echo "$(GREEN)✓ All tests passed$(NC)"; \
	else \
		echo "$(YELLOW)⚠ No test files found in $(TEST_DIR)$(NC)"; \
	fi

coverage:
	@echo "$(BLUE)Running tests with coverage...$(NC)"
	@if [ -d "$(TEST_DIR)" ] && [ "$$(find $(TEST_DIR) -name 'test_*.py' | wc -l)" -gt 0 ]; then \
		$(PYTEST) $(PYTEST_OPTS) $(COVERAGE_OPTS) $(TEST_DIR) || \
			(echo "$(RED)✗ Tests failed$(NC)" && exit 1); \
		echo "$(GREEN)✓ Coverage report generated in htmlcov/$(NC)"; \
		echo "$(YELLOW)→ Open htmlcov/index.html to view the report$(NC)"; \
	else \
		echo "$(YELLOW)⚠ No test files found in $(TEST_DIR)$(NC)"; \
	fi

watch:
	@echo "$(BLUE)Running tests in watch mode...$(NC)"
	@if command -v ptw &> /dev/null; then \
		ptw -- $(PYTEST_OPTS) $(TEST_DIR); \
	else \
		echo "$(YELLOW)pytest-watch not installed. Install with: pip install pytest-watch$(NC)"; \
		exit 1; \
	fi

#============================================================================
# Documentation
#============================================================================

docs:
	@echo "$(BLUE)Checking documentation...$(NC)"
	@if [ ! -f "README.md" ]; then \
		echo "$(RED)✗ README.md not found$(NC)"; \
		exit 1; \
	fi
	@if [ ! -f "CHANGELOG.md" ]; then \
		echo "$(YELLOW)⚠ CHANGELOG.md not found$(NC)"; \
	fi
	@if [ ! -d "$(DOCS_DIR)" ]; then \
		echo "$(YELLOW)⚠ docs/ directory not found$(NC)"; \
	fi
	@echo "$(GREEN)✓ Documentation check complete$(NC)"

#============================================================================
# Build and Release
#============================================================================

clean:
	@echo "$(BLUE)Cleaning up build artifacts and virtual environment...$(NC)"
	rm -rf build/ dist/ *.egg-info/ __pycache__/ .pytest_cache/ .coverage htmlcov/ .mypy_cache/ .venv-verify/ $(VENV_DIR)/
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".*.swp" -delete
	find . -type f -name ".coverage.*" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg" -exec rm -rf {} + 2>/dev/null || true
	@echo "$(GREEN)✓ Cleanup complete$(NC)"

version:
	@echo "$(BLUE)Current version information:$(NC)"
	@echo "Version in pyproject.toml: $$(grep -m 1 'version = ' pyproject.toml | cut -d '"' -f 2)"
	@echo "Version in __init__.py:     $$(grep '__version__' $(SRC_DIR)/$(PACKAGE_NAME)/__init__.py | cut -d '"' -f 2)"

build: clean
	@echo "$(BLUE)Building package...$(NC)"
	$(PYTHON) -m build || (echo "$(RED)✗ Build failed$(NC)" && exit 1)
	@echo "$(GREEN)✓ Package built successfully$(NC)"
	@ls -lh dist/

dist: build

release:
	@echo "$(BLUE)Starting release process...$(NC)"
	@$(MAKE) version
	@echo ""
	@read -p "Enter new version (e.g., 1.0.1): " version; \
	if [ -z "$$version" ]; then \
		echo "$(RED)✗ Version cannot be empty$(NC)"; \
		exit 1; \
	fi; \
	echo "$(YELLOW)Updating version to $$version...$(NC)"; \
	$(PYTHON) scripts/release.py $$version || exit 1; \
	echo "$(GREEN)✓ Version updated to $$version$(NC)"; \
	echo "$(YELLOW)Next steps:$(NC)"; \
	echo "  1. Review changes: git diff"; \
	echo "  2. Commit: git commit -am 'Bump version to $$version'"; \
	echo "  3. Tag: git tag -a v$$version -m 'Release v$$version'"; \
	echo "  4. Push: git push && git push --tags"

publish-test: verify build
	@echo "$(BLUE)Publishing to TestPyPI...$(NC)"
	$(TWINE) check dist/* || (echo "$(RED)✗ Package verification failed$(NC)" && exit 1)
	$(TWINE) upload --repository-url https://test.pypi.org/legacy/ dist/* || \
		(echo "$(RED)✗ Upload to TestPyPI failed$(NC)" && exit 1)
	@echo "$(GREEN)✓ Successfully published to TestPyPI$(NC)"

publish: verify build
	@echo "$(RED)⚠⚠⚠ WARNING: Publishing to PyPI (production) ⚠⚠⚠$(NC)"
	@read -p "Are you sure you want to publish to PyPI? [y/N] " -n 1 -r; \
	echo; \
	if [[ ! $$REPLY =~ ^[Yy]$$ ]]; then \
		echo "$(YELLOW)Publication cancelled$(NC)"; \
		exit 1; \
	fi
	@echo "$(BLUE)Publishing to PyPI...$(NC)"
	$(TWINE) check dist/* || (echo "$(RED)✗ Package verification failed$(NC)" && exit 1)
	$(TWINE) upload dist/* || (echo "$(RED)✗ Upload to PyPI failed$(NC)" && exit 1)
	@echo "$(GREEN)✓ Successfully published to PyPI$(NC)"

#============================================================================
# Composite Commands
#============================================================================

all: verify coverage
	@echo ""
	@echo "$(GREEN)✓✓✓ All checks and tests completed successfully! ✓✓✓$(NC)"
