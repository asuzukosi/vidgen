# Core Module Tests

This directory contains comprehensive unit tests for all core modules in the vidgen project.

## Running Tests

### Run all tests
```bash
pytest
```

### Run tests for a specific module
```bash
pytest core/tests/test_config_loader.py
pytest core/tests/test_pdf_parser.py
pytest core/tests/test_logger.py
```

### Run tests with verbose output
```bash
pytest -v
```

### Run tests with coverage report
```bash
pytest --cov=core --cov-report=html --cov-report=term
```

### Run specific test classes or functions
```bash
pytest core/tests/test_config_loader.py::TestConfig
pytest core/tests/test_logger.py::TestLogger::test_get_logger
```

## Test Structure

Each module in `core/` has a corresponding test file in `core/tests/`:

- `test_config_loader.py` - Tests for configuration management
- `test_logger.py` - Tests for logging functionality
- `test_pdf_parser.py` - Tests for PDF parsing
- `test_image_extractor.py` - Tests for image extraction from PDFs
- `test_image_labeler.py` - Tests for AI-powered image labeling
- `test_content_analyzer.py` - Tests for content analysis and segmentation
- `test_script_generator.py` - Tests for script generation
- `test_stock_image_fetcher.py` - Tests for stock image fetching
- `test_video_utils.py` - Tests for video utility functions
- `test_voiceover_generator.py` - Tests for voiceover generation

## Test Dependencies

The tests require the following packages:
- `pytest` - Testing framework
- `pytest-cov` (optional) - Coverage reporting
- `pytest-mock` (optional) - Enhanced mocking

Install test dependencies:
```bash
pip install pytest pytest-cov pytest-mock
```

## Fixtures

Common fixtures are defined in `conftest.py`:
- `project_root_dir` - Project root directory path
- `sample_pdf_path` - Temporary PDF file path
- `sample_image_path` - Temporary image file
- `mock_api_keys` - Mocked API keys
- `clean_environment` - Clean environment without API keys
- `sample_video_outline` - Sample video outline data
- `sample_script_data` - Sample script data
- `sample_images_metadata` - Sample image metadata

## Writing New Tests

When adding new functionality to core modules:

1. Create tests in the corresponding test file
2. Use appropriate fixtures from `conftest.py`
3. Mock external API calls and file I/O when possible
4. Follow the existing test structure and naming conventions
5. Aim for high test coverage of critical paths

Example test structure:
```python
class TestNewFeature:
    """Test suite for new feature."""
    
    def test_basic_functionality(self):
        """Test basic functionality."""
        # Arrange
        input_data = "test"
        
        # Act
        result = new_function(input_data)
        
        # Assert
        assert result == expected_output
```

## Continuous Integration

These tests are designed to run in CI/CD pipelines. Ensure all tests pass before merging changes.

