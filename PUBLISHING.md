# Publishing Guide for MotionMiner

This guide explains how to publish MotionMiner to PyPI and manage releases using automated versioning.

## 🚀 Quick Start

1. **Create Git Tag**: Create a git tag with the version number (e.g., `v1.1.0`)
2. **Create GitHub Release**: Create a GitHub release using the tag
3. **Automatic Publishing**: GitHub Actions will automatically build and publish to PyPI

**No manual version file updates needed!** setuptools-scm automatically generates version numbers from git tags.

## 📋 Prerequisites

### 1. PyPI Trusted Publisher Setup (Recommended)

1. Create a PyPI account at [PyPI](https://pypi.org/account/register/)
2. Enable 2FA (Two-Factor Authentication)
3. Set up Trusted Publishers:
   - Go to your project settings on PyPI
   - Add GitHub as a trusted publisher:
     - **Owner**: `mlapaglia`
     - **Repository**: `MotionMiner`
     - **Workflow**: `ci-cd.yml`
   - For TestPyPI: Do the same at [Test PyPI](https://test.pypi.org/)

## 🔄 Release Process

### GitHub Releases with Git Tags

1. **Create and Push Git Tag**:
   ```bash
   # Create a new tag for the version
   git tag v1.1.0
   
   # Push the tag to GitHub
   git push origin v1.1.0
   ```

2. **Create GitHub Release**:
   - Go to GitHub → Releases → Create a new release
   - Select the tag you just created: `v1.1.0`
   - Release title: `Release v1.1.0`
   - Add release notes describing changes
   - Click "Publish release"

3. **Automatic Publishing**:
   - GitHub Actions will automatically:
     - Run tests on multiple Python versions
     - Build the package with version `1.1.0` (from the git tag)
     - Publish to PyPI

## 🤖 Automated Version Management

### How It Works

MotionMiner uses **setuptools-scm** for automated version management:

- **Git Tags** → **Package Versions**
- `v1.0.0` → `1.0.0`
- `v1.1.0` → `1.1.0`
- `v2.0.0a1` → `2.0.0a1` (pre-release)

### Version Generation

```bash
# Tagged commit
git tag v1.1.0  → Package version: 1.1.0

# Commits after tag (development)
# → Package version: 1.1.0.dev5+g1234567.d20250715
```

### Pre-releases

For pre-releases, use semantic versioning pre-release identifiers:

```bash
# Alpha release
git tag v1.1.0a1  → Package version: 1.1.0a1

# Beta release  
git tag v1.1.0b1  → Package version: 1.1.0b1

# Release candidate
git tag v1.1.0rc1  → Package version: 1.1.0rc1
```

## 📝 Version Management

### Semantic Versioning

Follow [SemVer](https://semver.org/) guidelines for git tags:

- **MAJOR**: `v2.0.0` - Incompatible API changes
- **MINOR**: `v1.1.0` - New functionality (backward compatible)
- **PATCH**: `v1.0.1` - Bug fixes (backward compatible)

### No Manual Version Files

**✅ Automated**: setuptools-scm reads git tags  
**❌ Manual**: No more editing `_version.py` files  
**✅ Consistent**: Version is always in sync with git tags

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

### 2. Test PyPI (Automatic)

The workflow automatically publishes to TestPyPI on main branch pushes for testing:

```bash
# Install from Test PyPI
pip install --index-url https://test.pypi.org/simple/ motionminer

# Test the installation
motionminer --help
```

## 🔧 Configuration Files

### pyproject.toml

Key sections for automated versioning:

```toml
[build-system]
requires = ["setuptools>=61.0", "wheel", "setuptools-scm"]

[project]
dynamic = ["version"]

[tool.setuptools_scm]
version_scheme = "python-simplified-semver"
local_scheme = "node-and-date"
```

### GitHub Actions Workflow

Located at `.github/workflows/ci-cd.yml`:

- **Test Job**: Runs on multiple OS and Python versions
- **Build Job**: Creates distribution packages (triggered on releases and main pushes)
- **Test-Publish Job**: Uploads to TestPyPI (main branch pushes)
- **Publish Job**: Uploads to PyPI (all releases)

## 🚦 Release Checklist

### Before Release

- [ ] Run full test suite: `pytest tests/`
- [ ] Check linting: `flake8 motionminer/`
- [ ] Test build: `python -m build`
- [ ] Test installation: `pip install dist/motionminer-*.whl`
- [ ] Test CLI: `motionminer --help`
- [ ] Update CHANGELOG.md (if you have one)

### During Release

- [ ] Create and push git tag: `git tag v1.1.0 && git push origin v1.1.0`
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

1. **Version Not Updating**:
   - Ensure git tag is pushed: `git push origin v1.1.0`
   - Check tag format: Use `v1.1.0` not `1.1.0`
   - Verify setuptools-scm is installed in build environment

2. **Build Failures**:
   - Check import statements are correct
   - Verify all dependencies are listed in `pyproject.toml`
   - Ensure all files are included in package

3. **PyPI Upload Failures**:
   - Check Trusted Publisher setup is correct
   - Verify package name isn't already taken
   - Ensure version number is higher than existing releases

4. **GitHub Actions Failures**:
   - Check secrets are correctly set (if using API tokens)
   - Verify workflow file syntax
   - Review action logs for specific errors

### Version Debugging

```bash
# Check current version
python -c "import motionminer; print(motionminer.__version__)"

# Check what setuptools-scm would generate
python -m setuptools_scm
```

## 📚 Additional Resources

- [setuptools-scm Documentation](https://setuptools-scm.readthedocs.io/)
- [Semantic Versioning](https://semver.org/)
- [Python Packaging Guide](https://packaging.python.org/)
- [PyPI Trusted Publishers](https://docs.pypi.org/trusted-publishers/)
- [GitHub Actions for Python](https://docs.github.com/en/actions/automating-builds-and-tests/building-and-testing-python) 