.PHONY: clean install test fmt lint docs build dist

# Project settings
PACKAGE_NAME = lazyssh

# Tools
PYTHON = python3
PIP = pip
BLACK = black
ISORT = isort
PYLINT = pylint
PYTEST = pytest

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
	$(PYTHON) setup.py build

dist: clean
	$(PYTHON) setup.py sdist bdist_wheel 