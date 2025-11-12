# VidGen Testing Guide

## Quick Start

### Install Test Dependencies

```bash
pip install -r requirements-test.txt
```

Or install individually:
```bash
pip install pytest pytest-cov pytest-mock
```

### Run All Tests

```bash
pytest
```

### Run with Coverage

```bash
pytest --cov=core --cov-report=html --cov-report=term
```

View coverage report:
```bash
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

## Test Structure

```
core/tests/
├── __init__.py                      # Package marker
├── conftest.py                      # Shared fixtures and configuration
├── README.md                        # Detailed testing documentation
├── test_config_loader.py           # Config management tests
├── test_logger.py                  # Logging functionality tests
├── test_pdf_parser.py              # PDF parsing tests
├── test_image_extractor.py         # Image extraction tests
├── test_image_labeler.py           # AI image labeling tests
├── test_content_analyzer.py        # Content analysis tests
├── test_script_generator.py        # Script generation tests
├── test_stock_image_fetcher.py     # Stock image fetching tests
├── test_video_utils.py             # Video utility tests
└── test_voiceover_generator.py     # Voiceover generation tests
```

## Common Test Commands

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest core/tests/test_config_loader.py

# Run specific test class
pytest core/tests/test_logger.py::TestLogger

# Run specific test function
pytest core/tests/test_pdf_parser.py::TestPDFParser::test_extract_text

# Run tests matching pattern
pytest -k "test_initialization"

# Run tests and stop at first failure
pytest -x

# Run tests with detailed output
pytest -vv

# Run tests in parallel (requires pytest-xdist)
pytest -n auto
```

## Test Coverage by Module

| Module | Test File | Coverage |
|--------|-----------|----------|
| config_loader.py | test_config_loader.py | Configuration, env vars, API keys |
| logger.py | test_logger.py | Logging, colors, file rotation |
| pdf_parser.py | test_pdf_parser.py | Text extraction, structure detection |
| image_extractor.py | test_image_extractor.py | Image extraction, metadata |
| image_labeler.py | test_image_labeler.py | AI labeling, vision API |
| content_analyzer.py | test_content_analyzer.py | Content analysis, segmentation |
| script_generator.py | test_script_generator.py | Script generation, prompts |
| stock_image_fetcher.py | test_stock_image_fetcher.py | API integration, downloading |
| video_utils.py | test_video_utils.py | Video utilities, rendering |
| voiceover_generator.py | test_voiceover_generator.py | TTS, audio generation |

## Writing New Tests

### Example Test Structure

```python
import pytest
from core.your_module import YourClass

class TestYourClass:
    """Test suite for YourClass."""
    
    @pytest.fixture
    def instance(self):
        """Create a test instance."""
        return YourClass()
    
    def test_basic_functionality(self, instance):
        """Test basic functionality."""
        # Arrange
        input_data = "test"
        
        # Act
        result = instance.process(input_data)
        
        # Assert
        assert result == expected_output
    
    def test_error_handling(self, instance):
        """Test error handling."""
        with pytest.raises(ValueError):
            instance.process(None)
```

### Using Fixtures

```python
def test_with_fixtures(mock_api_keys, sample_pdf_path, tmp_path):
    """Test using common fixtures."""
    # mock_api_keys provides mocked environment variables
    # sample_pdf_path provides a temporary PDF path
    # tmp_path provides a temporary directory
    pass
```

## Available Fixtures (from conftest.py)

- `project_root_dir` - Project root directory path
- `sample_pdf_path` - Temporary PDF file path for testing
- `sample_image_path` - Temporary image file for testing
- `mock_api_keys` - Mocked API keys in environment
- `clean_environment` - Clean environment without API keys
- `sample_video_outline` - Sample video outline data structure
- `sample_script_data` - Sample script data structure
- `sample_images_metadata` - Sample image metadata

## Continuous Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        pip install -r requirements-test.txt
    
    - name: Run tests
      run: |
        pytest --cov=core --cov-report=xml --cov-report=term
    
    - name: Upload coverage
      uses: codecov/codecov-action@v2
      with:
        file: ./coverage.xml
```

## Troubleshooting

### Tests fail with import errors
```bash
# Make sure you're in the project root
cd /path/to/vidgen

# Ensure dependencies are installed
pip install -r requirements-test.txt

# Try running with Python module syntax
python -m pytest
```

### Tests fail with missing API keys
The tests use mocked API keys by default. If you see API key errors:
- Check that fixtures are properly imported
- Ensure `mock_api_keys` fixture is used
- Verify conftest.py is in the tests directory

### Slow test execution
```bash
# Run tests in parallel (requires pytest-xdist)
pip install pytest-xdist
pytest -n auto

# Run only fast tests (if marked)
pytest -m "not slow"
```

## Best Practices

1. **Run tests before committing**
   ```bash
   pytest
   ```

2. **Check coverage regularly**
   ```bash
   pytest --cov=core --cov-report=term-missing
   ```

3. **Write tests for new features** - Add tests in the corresponding test file

4. **Update tests when changing code** - Keep tests in sync with implementation

5. **Use descriptive test names** - Test names should explain what they test

6. **Mock external dependencies** - Use mocks for APIs, file I/O, etc.

7. **Keep tests independent** - Tests should not depend on each other

## Additional Resources

- [pytest documentation](https://docs.pytest.org/)
- [pytest-cov documentation](https://pytest-cov.readthedocs.io/)
- [Testing Best Practices](https://docs.python-guide.org/writing/tests/)
- See `core/tests/README.md` for detailed information
- See `.claude_docs/test_suite_documentation.md` for implementation details

