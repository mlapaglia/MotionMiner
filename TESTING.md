# MotionMiner Test Suite

This document describes the comprehensive test suite for the MotionMiner application.

## Overview

The test suite provides thorough coverage of all MotionMiner components and functionality, including:

- **197 Total Tests** across 8 test modules
- **93% Code Coverage** with detailed reporting
- **Unit Tests**: Test individual functions and classes in isolation
- **Integration Tests**: Test complete workflows and component interactions
- **Edge Case Testing**: Handle error conditions and boundary cases
- **Mock Testing**: Test external dependencies (ffmpeg) without requiring them

## Test Structure

```
tests/
├── test_analyzer.py         # File analysis functionality (21 tests)
├── test_cli.py              # Command-line interface (31 tests)
├── test_config.py           # Configuration and data structures (12 tests)
├── test_convert.py          # Convert module functionality (34 tests)
├── test_converter.py        # Video conversion features (26 tests)
├── test_extractor.py        # Motion photo extraction logic (20 tests)
├── test_integration.py      # End-to-end integration tests (22 tests)
├── test_main.py             # Main application workflow (31 tests)
├── pytest.ini              # Pytest configuration
└── __init__.py              # Package initialization
```

## Prerequisites

### Install Dependencies

```bash
# Install runtime dependencies
pip install -r requirements.txt

# Or install in development mode with test dependencies
pip install -e .[dev]
```

Test dependencies include:
- `pytest>=7.0.0` - Testing framework
- `pytest-cov>=4.0.0` - Coverage reporting
- `pytest-mock>=3.10.0` - Enhanced mocking capabilities

### Verify Installation

```bash
python -m pytest --version
pytest --version
```

## Running Tests

### Quick Start

```bash
# Run all tests with coverage
python -m pytest

# Run tests with verbose output
python -m pytest -v

# Run specific test file
python -m pytest tests/test_cli.py

# Run specific test class
python -m pytest tests/test_cli.py::TestCLI

# Run specific test method
python -m pytest tests/test_cli.py::TestCLI::test_parse_args_minimal
```

### Coverage Options

```bash
# Run tests with coverage report
python -m pytest --cov=motionminer --cov-report=term-missing

# Generate HTML coverage report
python -m pytest --cov=motionminer --cov-report=html

# View HTML coverage report
open htmlcov/index.html
```

### Test Categories

```bash
# Run unit tests only
python -m pytest -m unit

# Run integration tests only
python -m pytest -m integration

# Skip slow tests
python -m pytest -m "not slow"
```

## Test Coverage

### Current Coverage (93%)

| Module | Coverage | Tests | Key Coverage Areas |
|--------|----------|-------|-------------------|
| `analyzer.py` | 100% | 21 | File analysis, marker detection, reporting |
| `cli.py` | 99% | 31 | Argument parsing, validation, help text |
| `config.py` | 100% | 12 | Data structures, constants, validation |
| `convert.py` | 86% | 34 | MP4 extraction, conversion, batch processing |
| `converter.py` | 99% | 26 | Video conversion, quality settings, ffmpeg |
| `extractor.py` | 95% | 20 | Motion photo extraction, file handling |
| `main.py` | 99% | 31 | Application workflow, error handling |
| `__init__.py` | 88% | - | Package initialization |

### Detailed Test Scenarios

#### Configuration Tests (`test_config.py`)
**12 tests covering:**
- ✅ `Settings` data class creation and validation
- ✅ GIF quality preset validation (`tiny`, `low`, `medium`, `high`)
- ✅ Default value verification
- ✅ File extension support (`.jpg`, `.jpeg`, `.JPG`, `.JPEG`)
- ✅ Marker constant validation
- ✅ Configuration object immutability

#### CLI Tests (`test_cli.py`)
**31 tests covering:**
- ✅ Command-line argument parsing (`parse_args`)
- ✅ Mutually exclusive options validation
- ✅ Input path validation and expansion
- ✅ Output format detection and validation
- ✅ Batch mode configuration
- ✅ Analysis-only mode
- ✅ Quality preset validation
- ✅ Width/height parameter parsing
- ✅ Help text generation and accuracy
- ✅ Error handling for invalid combinations

#### Extractor Tests (`test_extractor.py`)
**20 tests covering:**
- ✅ `MotionExtractor` class initialization
- ✅ Motion photo validation (`is_motion_photo`)
- ✅ MP4 detection in JPEG files
- ✅ Binary data extraction (`extract_video`)
- ✅ Temporary file management
- ✅ Error handling for corrupted files
- ✅ File cleanup on object destruction
- ✅ Complete extraction workflow
- ✅ Edge cases (empty files, invalid formats)

#### Analyzer Tests (`test_analyzer.py`)
**21 tests covering:**
- ✅ File structure analysis
- ✅ Motion photo marker detection
- ✅ MP4 signature identification
- ✅ File section breakdown and analysis
- ✅ Summary report generation
- ✅ Error handling for invalid files
- ✅ Different file format handling
- ✅ Edge cases (empty files, corrupted data)

#### Convert Tests (`test_convert.py`)
**34 tests covering:**
- ✅ `find_mp4_in_jpg` function for MP4 detection
- ✅ `get_video_fps` function for frame rate detection
- ✅ `convert_mp4_to_gif` function for video conversion
- ✅ `extract_mp4_from_jpg` function for extraction
- ✅ `analyze_jpg_structure` function for file analysis
- ✅ `batch_extract` function for bulk processing
- ✅ Command-line interface (`main` function)
- ✅ Error handling for all functions
- ✅ File operations and cleanup
- ✅ Different output formats (MP4, GIF, both)

#### Converter Tests (`test_converter.py`)
**26 tests covering:**
- ✅ `VideoConverter` class initialization
- ✅ Video format conversion (`convert_to_gif`)
- ✅ FPS detection and handling
- ✅ Quality preset application
- ✅ ffmpeg command generation
- ✅ Fallback conversion methods
- ✅ Temporary file management and cleanup
- ✅ Error handling for missing ffmpeg
- ✅ Different quality settings
- ✅ Custom width/height parameters

#### Main Application Tests (`test_main.py`)
**31 tests covering:**
- ✅ Complete application workflow (`main` function)
- ✅ Single file processing
- ✅ Batch processing with directory scanning
- ✅ Analysis-only mode
- ✅ Error handling and cleanup
- ✅ Signal handling (Ctrl+C)
- ✅ Exit code generation
- ✅ File validation and filtering
- ✅ Output directory creation
- ✅ Progress reporting

#### Integration Tests (`test_integration.py`)
**22 tests covering:**
- ✅ End-to-end MP4 extraction workflow
- ✅ End-to-end GIF conversion workflow
- ✅ Batch processing complete workflows
- ✅ Error scenario handling
- ✅ Real-world usage patterns
- ✅ External dependency mocking
- ✅ File system integration
- ✅ Command-line to output integration

## Mock Testing Strategy

### External Dependencies

The test suite uses comprehensive mocking to avoid external dependencies:

#### ffmpeg Mocking
```python
# Mock subprocess calls to ffmpeg
with patch('subprocess.run') as mock_run:
    mock_run.return_value = MagicMock(returncode=0, stdout="30/1")
    # Test video conversion without requiring ffmpeg
```

#### File System Mocking
```python
# Mock file operations for edge cases
with patch('builtins.open', side_effect=OSError("No space left")):
    # Test disk space error handling
```

#### Path Mocking
```python
# Mock file existence checks
with patch('pathlib.Path.exists', return_value=True):
    # Test file validation logic
```

### Test Data Creation

The test suite creates realistic mock data:

```python
def create_mock_motion_photo(self, filename: str) -> Path:
    """Create realistic motion photo for testing"""
    jpeg_header = b'\xff\xd8\xff\xe0\x00\x10JFIF'
    jpeg_data = b'x' * 50000  # 50KB of image data
    jpeg_end = b'\xff\xd9'
    
    # Add motion photo markers
    motion_markers = b'GCamera:MicroVideo' + b'Google'
    
    # Create MP4 data with proper structure
    mp4_size = struct.pack('>I', 1000)
    mp4_data = mp4_size + b'ftyp' + b'mp42' + b'x' * 988
    
    full_data = jpeg_header + jpeg_data + jpeg_end + motion_markers + mp4_data
    # Save to temporary file for testing
```

## Error Testing

### Comprehensive Error Scenarios

The test suite covers various error conditions:

#### File System Errors
- ✅ Non-existent files
- ✅ Permission denied errors
- ✅ Disk space issues
- ✅ Corrupted files
- ✅ Invalid file formats
- ✅ Read/write failures

#### Application Errors
- ✅ Invalid command-line arguments
- ✅ Missing dependencies (ffmpeg)
- ✅ Extraction failures
- ✅ Conversion failures
- ✅ Unexpected exceptions
- ✅ Network/subprocess failures

#### User Interaction Errors
- ✅ Keyboard interrupts (Ctrl+C)
- ✅ Invalid input combinations
- ✅ Empty batch directories
- ✅ Unsupported file types
- ✅ Configuration conflicts

## Performance Testing

### Test Execution Speed

The test suite is optimized for speed:

```bash
# Measure test execution time
time python -m pytest

# Typical execution time: ~0.7 seconds for 197 tests
```

### Memory Usage
The test suite monitors memory usage and cleans up properly:
- Temporary files are removed after each test
- Mock objects are reset between tests
- File handles are properly closed
- Memory leaks are prevented

## Continuous Integration

### GitHub Actions Integration
The test suite is configured for CI/CD environments:

```yaml
# .github/workflows/ci-cd.yml
- name: Test with pytest
  run: |
    pytest tests/ --cov --junitxml=junit.xml -o junit_family=legacy
```

### Coverage Reporting
- **Terminal coverage**: Real-time coverage during test runs
- **HTML coverage**: Detailed line-by-line coverage reports
- **XML coverage**: For CI/CD integration
- **Missing lines**: Identifies uncovered code

## Configuration

### pytest.ini Configuration
```ini
[tool:pytest]
testpaths = .
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --tb=short
    --strict-markers
    --strict-config
    --disable-warnings
    --cov=.
    --cov-report=term-missing
    --cov-report=html:htmlcov
    --cov-exclude=test_*
    --cov-exclude=*/__pycache__/*
markers =
    unit: Unit tests for individual components
    integration: Integration tests for complete workflows
    slow: Tests that take a long time to run
```

## Adding New Tests

### Test File Naming
- Use `test_` prefix: `test_new_module.py`
- Match module names: `test_module.py` for `module.py`
- Place in `tests/` directory

### Test Class Structure
```python
class TestNewFeature:
    """Test new feature functionality"""
    
    def setup_method(self):
        """Setup before each test"""
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Cleanup after each test"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_feature_success(self):
        """Test successful feature operation"""
        # Arrange
        # Act
        # Assert
        
    def test_feature_error(self):
        """Test feature error handling"""
        # Arrange
        # Act  
        # Assert
```

### Test Naming Conventions
- Use descriptive names: `test_parse_args_with_custom_width`
- Include scenario: `test_conversion_fails_gracefully`
- Be specific: `test_batch_processing_empty_directory`

## Troubleshooting

### Common Issues

#### Pytest Not Found
```bash
pip install pytest pytest-cov pytest-mock
```

#### Import Errors
```bash
# Make sure you're in the project directory
cd /path/to/MotionMiner
python -m pytest tests/
```

#### Coverage Issues
```bash
# Install coverage dependencies
pip install pytest-cov

# Run with explicit coverage
python -m pytest --cov=motionminer
```

### Debugging Tests

#### Run Single Test with Verbose Output
```bash
python -m pytest tests/test_cli.py::TestCLI::test_parse_args_minimal -v -s
```

#### Debug with Print Statements
```python
def test_debug_example(self):
    result = some_function()
    print(f"Debug: result = {result}")  # Use -s flag to see output
    assert result == expected
```

#### Use Debugger
```python
def test_with_debugger(self):
    import pdb; pdb.set_trace()
    # Test code here
```

## Best Practices

### Test Organization
- ✅ One test file per module
- ✅ Logical test class grouping
- ✅ Clear, descriptive test names
- ✅ Proper setup/teardown

### Test Quality
- ✅ Test both success and failure cases
- ✅ Use realistic test data
- ✅ Mock external dependencies
- ✅ Clean up resources

### Maintainability
- ✅ Keep tests independent
- ✅ Use helper methods for common setup
- ✅ Document complex test scenarios
- ✅ Regular test suite maintenance

## Coverage Goals

Target coverage levels:
- **Overall**: 90%+ (Current: 93% ✅)
- **Unit Tests**: 95%+ (Current: 95%+ ✅)
- **Critical Paths**: 100% (analyzer.py, config.py ✅)
- **Error Handling**: 100% (Comprehensive ✅)

Current detailed coverage by module:
- analyzer.py: 100%
- cli.py: 99%
- config.py: 100%
- convert.py: 86%
- converter.py: 99%
- extractor.py: 95%
- main.py: 99%

## Running the Complete Test Suite

```bash
# Run all tests with coverage
python -m pytest tests/ --cov=motionminer --cov-report=term-missing

# Expected output:
# 197 passed in ~0.7s
# Coverage: 93%
```

---

For questions about the test suite, please refer to the individual test files or the main project documentation. 