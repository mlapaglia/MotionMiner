# MotionMiner Test Suite

This document describes the comprehensive test suite for the MotionMiner application.

## Overview

The test suite provides thorough coverage of all MotionMiner components and functionality, including:

- **Unit Tests**: Test individual functions and classes in isolation
- **Integration Tests**: Test complete workflows and component interactions
- **Edge Case Testing**: Handle error conditions and boundary cases
- **Mock Testing**: Test external dependencies (ffmpeg) without requiring them

## Test Structure

```
MotionMiner/
├── test_config.py          # Configuration and data structures
├── test_cli.py             # Command-line interface
├── test_extractor.py       # Motion photo extraction logic
├── test_analyzer.py        # File analysis functionality
├── test_converter.py       # Video conversion features
├── test_main.py            # Main application workflow
├── test_integration.py     # End-to-end integration tests
├── pytest.ini             # Pytest configuration
├── run_tests.py            # Test runner script
└── TESTING.md              # This documentation
```

## Prerequisites

### Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- `pytest>=7.0.0` - Testing framework
- `pytest-cov>=4.0.0` - Coverage reporting
- `pytest-mock>=3.10.0` - Enhanced mocking capabilities
- `ffmpeg-python` - Video processing (for the main application)

### Verify Installation

```bash
python -m pytest --version
```

## Running Tests

### Quick Start

```bash
# Run all tests with coverage
python run_tests.py

# Or use pytest directly
python -m pytest
```

### Test Categories

#### Unit Tests
Test individual components in isolation:
```bash
python run_tests.py --unit
```

#### Integration Tests
Test complete workflows:
```bash
python run_tests.py --integration
```

#### Fast Tests Only
Skip time-consuming tests:
```bash
python run_tests.py --fast
```

### Specific Test Files

```bash
# Test specific module
python run_tests.py test_config.py
python run_tests.py test_cli.py
python run_tests.py test_extractor.py

# Test specific test class
python run_tests.py test_cli.py::TestCLI

# Test specific test method
python run_tests.py test_cli.py::TestCLI::test_parse_args_minimal
```

### Coverage Options

```bash
# Run tests without coverage (faster)
python run_tests.py --no-coverage

# Run with detailed coverage report
python -m pytest --cov=. --cov-report=html
```

## Test Coverage

### Module Coverage

| Module | Test File | Coverage Focus |
|--------|-----------|----------------|
| `config.py` | `test_config.py` | Data structures, constants, validation |
| `cli.py` | `test_cli.py` | Argument parsing, validation, help text |
| `extractor.py` | `test_extractor.py` | MP4 detection, extraction, file handling |
| `analyzer.py` | `test_analyzer.py` | File analysis, marker detection, reporting |
| `converter.py` | `test_converter.py` | Video conversion, quality settings, ffmpeg |
| `main.py` | `test_main.py` | Application workflow, error handling |
| All modules | `test_integration.py` | End-to-end workflows, real scenarios |

### Key Test Scenarios

#### Configuration Tests (`test_config.py`)
- ✅ Data class creation and validation
- ✅ GIF quality preset validation
- ✅ Default value verification
- ✅ File extension support
- ✅ Marker constant validation

#### CLI Tests (`test_cli.py`)
- ✅ Command-line argument parsing
- ✅ Mutually exclusive options
- ✅ Configuration validation
- ✅ Help text generation
- ✅ Error handling for invalid inputs
- ✅ Batch mode validation
- ✅ Output format detection

#### Extractor Tests (`test_extractor.py`)
- ✅ Motion photo validation
- ✅ MP4 detection in JPEG files
- ✅ Binary data extraction
- ✅ Temporary file management
- ✅ Error handling for corrupted files
- ✅ File cleanup on destruction
- ✅ Complete extraction workflow

#### Analyzer Tests (`test_analyzer.py`)
- ✅ File structure analysis
- ✅ Motion photo marker detection
- ✅ MP4 signature identification
- ✅ File section breakdown
- ✅ Summary report generation
- ✅ Error handling for invalid files

#### Converter Tests (`test_converter.py`)
- ✅ Video format conversion
- ✅ FPS detection and handling
- ✅ Quality preset application
- ✅ ffmpeg command generation
- ✅ Fallback conversion methods
- ✅ Temporary file cleanup
- ✅ Error handling for missing ffmpeg

#### Main Application Tests (`test_main.py`)
- ✅ Complete application workflow
- ✅ Single file processing
- ✅ Batch processing
- ✅ Analysis-only mode
- ✅ Error handling and cleanup
- ✅ Signal handling (Ctrl+C)
- ✅ Exit code generation

#### Integration Tests (`test_integration.py`)
- ✅ End-to-end MP4 extraction
- ✅ End-to-end GIF conversion
- ✅ Batch processing workflows
- ✅ Error scenario handling
- ✅ Real-world usage patterns
- ✅ External dependency mocking

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
    # ... save to file
```

## Error Testing

### Comprehensive Error Scenarios

The test suite covers various error conditions:

#### File System Errors
- ✅ Non-existent files
- ✅ Permission denied
- ✅ Disk space issues
- ✅ Corrupted files
- ✅ Invalid file formats

#### Application Errors
- ✅ Invalid command-line arguments
- ✅ Missing dependencies (ffmpeg)
- ✅ Extraction failures
- ✅ Conversion failures
- ✅ Unexpected exceptions

#### User Interaction Errors
- ✅ Keyboard interrupts (Ctrl+C)
- ✅ Invalid input combinations
- ✅ Empty batch directories
- ✅ Unsupported file types

## Performance Testing

### Test Execution Speed

```bash
# Measure test execution time
time python run_tests.py

# Run only fast tests
python run_tests.py --fast
```

### Memory Usage
The test suite monitors memory usage and cleans up properly:
- Temporary files are removed after each test
- Mock objects are reset between tests
- File handles are properly closed

## Continuous Integration

### GitHub Actions Ready
The test suite is designed for CI/CD environments:

```yaml
# Example .github/workflows/test.yml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.8'
      - run: pip install -r requirements.txt
      - run: python run_tests.py
```

### Coverage Reporting
```bash
# Generate HTML coverage report
python -m pytest --cov=. --cov-report=html

# View coverage report
open htmlcov/index.html
```

## Adding New Tests

### Test File Naming
- Use `test_` prefix: `test_new_module.py`
- Match module names: `test_module.py` for `module.py`

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

### Mock Usage Guidelines
```python
# Mock external dependencies
with patch('subprocess.run') as mock_run:
    mock_run.return_value = MagicMock(returncode=0)
    # Test code

# Mock print statements for testing
with patch('builtins.print') as mock_print:
    # Code that prints
    mock_print.assert_called()

# Mock file operations
with patch('pathlib.Path.exists', return_value=True):
    # Test file handling
```

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
python -m pytest
```

#### Coverage Issues
```bash
# Install coverage dependencies
pip install pytest-cov
```

#### ffmpeg Warnings
The tests mock ffmpeg calls, so warnings about missing ffmpeg are expected and don't affect test results.

### Debugging Tests

#### Run Single Test with Verbose Output
```bash
python -m pytest test_cli.py::TestCLI::test_parse_args_minimal -v -s
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
- **Overall**: 90%+
- **Unit Tests**: 95%+
- **Critical Paths**: 100%
- **Error Handling**: 100%

Current coverage can be viewed by running:
```bash
python run_tests.py
```

The coverage report shows which lines are tested and which need additional coverage.

---

For questions about the test suite, please refer to the test files themselves or the main project documentation. 