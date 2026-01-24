.PHONY: help install run fmt fix lint test check build clean version release publish pre-commit pre-commit-install

SHELL := /bin/bash

# Colors
BLUE = \033[0;34m
GREEN = \033[0;32m
YELLOW = \033[1;33m
RED = \033[0;31m
NC = \033[0m

help:
	@echo -e "$(BLUE)LazySSH Development$(NC)"
	@echo "==================="
	@echo ""
	@echo -e "$(YELLOW)Prerequisites: pipx install hatch$(NC)"
	@echo ""
	@echo -e "$(GREEN)Development:$(NC)"
	@echo "  make install    Setup Hatch environment"
	@echo "  make run        Run lazyssh (hatch run lazyssh)"
	@echo "  make fmt        Format code (ruff format)"
	@echo "  make fix        Auto-fix and format (ruff check --fix + format)"
	@echo "  make lint       Run linter (ruff check)"
	@echo "  make test       Run tests with coverage"
	@echo "  make check      Run all quality checks"
	@echo ""
	@echo -e "$(GREEN)Git Hooks:$(NC)"
	@echo "  make pre-commit-install   Install pre-commit hooks"
	@echo "  make pre-commit           Run pre-commit on all files"
	@echo ""
	@echo -e "$(GREEN)Release:$(NC)"
	@echo "  make build      Build package"
	@echo "  make clean      Clean artifacts"
	@echo "  make version    Show version"
	@echo "  make release    Version bump workflow"
	@echo "  make publish    Publish to PyPI"

install:
	@echo -e "$(BLUE)Setting up environment...$(NC)"
	@command -v hatch >/dev/null 2>&1 || { echo -e "$(RED)Install hatch: pipx install hatch$(NC)"; exit 1; }
	@hatch env create default 2>/dev/null || true
	@echo -e "$(GREEN)Done! Run: make run$(NC)"

run:
	@hatch run lazyssh

fmt:
	@hatch run fmt

fix:
	@hatch run fix

lint:
	@hatch run lint

test:
	@hatch run test

check:
	@echo -e "$(BLUE)Running quality checks...$(NC)"
	@hatch run check
	@echo -e "$(GREEN)All checks passed$(NC)"

build:
	@rm -rf dist/
	@hatch build
	@hatch run verify-pkg

clean:
	@rm -rf build/ dist/ *.egg-info/ .pytest_cache/ .coverage htmlcov/ .mypy_cache/ .ruff_cache/
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@hatch env prune 2>/dev/null || true
	@echo -e "$(GREEN)Clean$(NC)"

version:
	@hatch version

release:
	@echo "Current: $$(hatch version)"
	@read -p "New version: " v && hatch version $$v && \
	echo -e "$(GREEN)Updated to $$v$(NC)" && \
	echo "Next: git commit -am 'v$$v' && git tag v$$v && git push --tags"

publish: check build
	@echo -e "$(RED)Publishing to PyPI$(NC)"
	@read -p "Continue? [y/N] " -n1 r; echo; [[ $$r == [Yy] ]] && hatch publish || echo "Cancelled"

pre-commit-install:
	@command -v pre-commit >/dev/null 2>&1 || { echo -e "$(RED)Install pre-commit: mise install$(NC)"; exit 1; }
	@pre-commit install
	@echo -e "$(GREEN)Pre-commit hooks installed$(NC)"

pre-commit:
	@pre-commit run --all-files
