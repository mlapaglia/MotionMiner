# Publishing Guide for MotionMiner

This guide explains how to publish MotionMiner to PyPI and manage releases.

## 🚀 Quick Start

1. **Update Version**: Update the version in `motionminer/_version.py`
2. **Create Release**: Create a GitHub release with a tag
3. **Automatic Publishing**: GitHub Actions will automatically build and publish to PyPI

## 📋 Prerequisites

### 1. PyPI Account Setup

1. Create accounts on both:
   - [PyPI](https://pypi.org/account/register/) (production)
   - [Test PyPI](https://test.pypi.org/account/register/) (testing)

2. Enable 2FA (Two-Factor Authentication) on both accounts

3. Create API tokens:
   - Go to Account Settings → API tokens
   - Create a token with "Entire account" scope
   - Save the token securely (you won't be able to see it again)

### 2. GitHub Repository Setup

1. Go to your GitHub repository → Settings → Secrets and variables → Actions

2. Add the following secrets:
   - `PYPI_API_TOKEN`: Your PyPI API token
   - `TEST_PYPI_API_TOKEN`: Your Test PyPI API token

3. Create environments (optional but recommended):
   - Go to Settings → Environments
   - Create environments named `pypi` and `test-pypi`
   - Add the respective secrets to each environment

## 🔄 Release Process

### Method 1: GitHub Releases (Recommended)

1. **Update Version**:
   ```bash
   # Edit motionminer/_version.py
   __version__ = "1.1.0"
   ```

2. **Commit Changes**:
   ```bash
   git add motionminer/_version.py
   git commit -m "Bump version to 1.1.0"
   git push origin main
   ```

3. **Create Release**:
   - Go to GitHub → Releases → Create a new release
   - Create a new tag: `v1.1.0`
   - Release title: `Release v1.1.0`
   - Add release notes describing changes
   - Click "Publish release"

4. **Automatic Publishing**:
   - GitHub Actions will automatically:
     - Run tests on multiple Python versions
     - Build the package
     - Publish to PyPI

### Method 2: Manual Publishing

1. **Install build tools**:
   ```bash
   pip install build twine
   ```

2. **Build the package**:
   ```bash
   python -m build
   ```

3. **Upload to Test PyPI first**:
   ```bash
   twine upload --repository testpypi dist/*
   ```

4. **Test the package**:
   ```bash
   pip install --index-url https://test.pypi.org/simple/ motionminer
   ```

5. **Upload to production PyPI**:
   ```bash
   twine upload dist/*
   ```

## 🧪 Testing Before Release

### 1. Local Testing

```bash
# Install in development mode
pip install -e .[dev]

# Run tests
pytest tests/

# Run linting
flake8 motionminer/

# Run type checking
mypy motionminer/

# Build and test package
python -m build
pip install dist/motionminer-*.whl
```

### 2. Test PyPI

```bash
# Upload to Test PyPI
twine upload --repository testpypi dist/*

# Install from Test PyPI
pip install --index-url https://test.pypi.org/simple/ motionminer

# Test the installation
motionminer --help
```

## 🔧 Configuration Files

### pyproject.toml

The main configuration file for the package. Key sections:

- `[project]`: Package metadata
- `[project.scripts]`: Console script entry points
- `[tool.setuptools]`: Package discovery and data files
- `[tool.pytest.ini_options]`: Test configuration

### GitHub Actions Workflow

Located at `.github/workflows/ci-cd.yml`:

- **Test Job**: Runs on multiple OS and Python versions
- **Build Job**: Creates distribution packages
- **Publish Job**: Uploads to PyPI on release
- **Publish-Test Job**: Uploads to Test PyPI for pre-releases

## 📝 Version Management

### Semantic Versioning

Follow [SemVer](https://semver.org/) guidelines:

- **MAJOR**: Incompatible API changes
- **MINOR**: New functionality (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Version File

Update `motionminer/_version.py`:

```python
__version__ = "1.2.3"
```

## 🚦 Release Checklist

### Before Release

- [ ] Update version in `motionminer/_version.py`
- [ ] Update CHANGELOG.md (if you have one)
- [ ] Run full test suite: `pytest tests/`
- [ ] Check linting: `flake8 motionminer/`
- [ ] Test build: `python -m build`
- [ ] Test installation: `pip install dist/motionminer-*.whl`
- [ ] Test CLI: `motionminer --help`

### During Release

- [ ] Create GitHub release with proper tag
- [ ] Add comprehensive release notes
- [ ] Monitor GitHub Actions for successful build
- [ ] Verify publication on PyPI

### After Release

- [ ] Test installation from PyPI: `pip install motionminer`
- [ ] Update documentation if needed
- [ ] Announce release (if applicable)

## 🔍 Troubleshooting

### Common Issues

1. **Build Failures**:
   - Check import statements are correct
   - Verify all dependencies are listed in `pyproject.toml`
   - Ensure all files are included in `MANIFEST.in`

2. **PyPI Upload Failures**:
   - Check API token is valid and has correct permissions
   - Verify package name isn't already taken
   - Ensure version number is higher than existing releases

3. **GitHub Actions Failures**:
   - Check secrets are correctly set
   - Verify workflow file syntax
   - Review action logs for specific errors

### Getting Help

- Check the [Python Packaging Guide](https://packaging.python.org/)
- Review [PyPI Help](https://pypi.org/help/)
- Check GitHub Actions [documentation](https://docs.github.com/en/actions)

## 📚 Additional Resources

- [Python Packaging Tutorial](https://packaging.python.org/tutorials/packaging-projects/)
- [setuptools Documentation](https://setuptools.pypa.io/)
- [GitHub Actions for Python](https://docs.github.com/en/actions/automating-builds-and-tests/building-and-testing-python)
- [PyPI Publishing with GitHub Actions](https://packaging.python.org/guides/publishing-package-distribution-releases-using-github-actions-ci-cd-workflows/) 