# Publishing to PyPI

This guide explains how to publish LazySSH to PyPI using GitHub Actions.

## Prerequisites

1. A PyPI account (register at [pypi.org](https://pypi.org/account/register/))
2. A TestPyPI account (register at [test.pypi.org](https://test.pypi.org/account/register/))
3. GitHub repository with GitHub Actions enabled

## Setting Up API Tokens

### PyPI Token

1. Log in to your PyPI account at [pypi.org](https://pypi.org/account/login/)
2. Go to Account Settings > API tokens
3. Create a new API token with the scope "Entire account (all projects)"
4. Copy the token (you won't be able to see it again)

### TestPyPI Token

1. Log in to your TestPyPI account at [test.pypi.org](https://test.pypi.org/account/login/)
2. Go to Account Settings > API tokens
3. Create a new API token with the scope "Entire account (all projects)"
4. Copy the token (you won't be able to see it again)

## Setting Up GitHub Secrets

1. Go to your GitHub repository
2. Navigate to Settings > Secrets and variables > Actions
3. Add the following secrets:
   - `PYPI_API_TOKEN`: Your PyPI API token
   - `TEST_PYPI_API_TOKEN`: Your TestPyPI API token

## Publishing Process

### Automatic Publishing (Recommended)

1. Update the version number using the release script:
   ```bash
   python scripts/release.py 1.0.1
   ```

2. Commit and push the changes:
   ```bash
   git commit -am "Bump version to 1.0.1"
   git push
   ```

3. Create a new release on GitHub:
   - Go to your repository on GitHub
   - Navigate to Releases > Draft a new release
   - Tag version: `v1.0.1` (must match the version in the code)
   - Release title: `v1.0.1`
   - Description: Add release notes
   - Click "Publish release"

4. The GitHub Actions workflow will automatically:
   - Run tests
   - Build the package
   - Publish to TestPyPI
   - Publish to PyPI

### Manual Publishing

If you need to publish manually:

1. Update the version number:
   ```bash
   python scripts/release.py 1.0.1 --no-tag
   ```

2. Build the package:
   ```bash
   python -m build
   ```

3. Check the package:
   ```bash
   twine check dist/*
   ```

4. Upload to TestPyPI:
   ```bash
   twine upload --repository-url https://test.pypi.org/legacy/ dist/*
   ```

5. Test the installation:
   ```bash
   pip install --index-url https://test.pypi.org/simple/ lazyssh
   ```

6. Upload to PyPI:
   ```bash
   twine upload dist/*
   ```

## Troubleshooting

### Version Conflicts

If you get an error about version conflicts, make sure:
- The version in `pyproject.toml`, `setup.py`, and `src/lazyssh/__init__.py` match
- You haven't already published this version to PyPI (you cannot overwrite existing versions)

### Authentication Issues

If you get authentication errors:
- Check that your API tokens are correct
- Ensure the GitHub secrets are properly set up
- Try publishing manually to debug the issue

### Package Content Issues

If your package is missing files:
- Check your `MANIFEST.in` file
- Run `python -m build` locally and inspect the resulting wheel and tarball 