.PHONY: clean install test fmt lint docs build dist release publish publish-test

# Project settings
PACKAGE_NAME = lazyssh

# Tools
PYTHON = python3
PIP = pip
BLACK = black
ISORT = isort
PYLINT = pylint
PYTEST = pytest
TWINE = twine

help:
	@echo "LazySSH Development Tasks"
	@echo "--------------------------"
	@echo "make install          Install the package in development mode"
	@echo "make test             Run tests"
	@echo "make fmt              Format code with Black and isort"
	@echo "make lint             Run linting with pylint"
	@echo "make clean            Clean up build artifacts"
	@echo "make build            Build the package"
	@echo "make dist             Build the distribution packages"
	@echo "make release          Update version numbers and create a Git tag"
	@echo "make publish-test     Publish to TestPyPI"
	@echo "make publish          Publish to PyPI"

clean:
	rm -rf build/ dist/ *.egg-info/ __pycache__/ .pytest_cache/ .coverage
	find . -name "__pycache__" -type d -exec rm -rf {} +
	find . -name "*.pyc" -type f -delete
	find . -name "*.pyo" -type f -delete
	find . -name "*.pyd" -type f -delete
	find . -name ".*.swp" -type f -delete
	find . -name ".coverage.*" -type f -delete

install:
	$(PIP) install -e .

test:
	$(PYTEST) tests/

fmt:
	$(ISORT) src/ tests/
	$(BLACK) src/ tests/

lint:
	$(PYLINT) src/

build: clean
	$(PYTHON) -m build

dist: build

release:
	@echo "Current version: $$(grep -m 1 'version = ' pyproject.toml | cut -d '"' -f 2)"
	@read -p "Enter new version (e.g., 1.0.1): " version; \
	$(PYTHON) scripts/release.py $$version

publish-test: dist
	$(TWINE) check dist/*
	$(TWINE) upload --repository-url https://test.pypi.org/legacy/ dist/*

publish: dist
	$(TWINE) check dist/*
	$(TWINE) upload dist/* 