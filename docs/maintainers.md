# Maintainers Guide

Operational notes for developing, testing, and releasing LazySSH. Contributor guidelines live in [CONTRIBUTING.md](../CONTRIBUTING.md).

## Local Development Setup
```bash
git clone https://github.com/Bochner/lazyssh.git
cd lazyssh
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pre-commit install
```
Useful scripts:
- `./pre-commit-check.sh` – runs black, isort, flake8, mypy, and pytest.
- `pytest` – run the test suite (tests live under `tests/`).

## Logging & Debugging
- Start LazySSH with verbose logging: `python -m lazyssh --debug` (set `PYTHONPATH=src` when running from the repo).
- Runtime logs are stored in `/tmp/lazyssh/logs/`:
  - `lazyssh_YYYYMMDD.log` – general lifecycle events
  - `lazyssh.ssh_YYYYMMDD.log` – SSH operations (connections, tunnels)
  - `lazyssh.command_YYYYMMDD.log` – interactive command activity
  - `lazyssh.scp_YYYYMMDD.log` – file transfer details
- Each connection also gets `/tmp/lazyssh/<socket>.d/logs/connection.log` for per-host activity.
- Toggle logging while running with `lazyssh> debug`.

## Packaging & Releases
1. Update the version using the release script (updates `pyproject.toml` and `src/lazyssh/__init__.py`):
   ```bash
   python scripts/release.py 1.2.3
   ```
2. Run the full pre-commit suite and tests.
3. Commit, push, and draft a GitHub release tagged `v1.2.3` with notes.
4. The GitHub Actions workflow builds, tests, and publishes to TestPyPI and PyPI using repository secrets (`PYPI_API_TOKEN`, `TEST_PYPI_API_TOKEN`).
5. For manual publishing (fallback):
   ```bash
   python -m build
   twine check dist/*
   twine upload --repository-url https://test.pypi.org/legacy/ dist/*
   twine upload dist/*
   ```

## Useful Paths & Utilities
- Saved configurations: `/tmp/lazyssh/connections.conf` (permissions `600`).
- Runtime plugin directory: `/tmp/lazyssh/plugins` (created automatically, permissions `700`).
- Inspect Rich console behaviour in `src/lazyssh/console_instance.py` for theme-related changes.
