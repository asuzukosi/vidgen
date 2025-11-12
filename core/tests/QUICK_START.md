# Quick Start - Running Tests

## 1. Install pytest

```bash
pip install pytest pytest-cov pytest-mock
```

Or install all test dependencies:
```bash
pip install -r requirements-test.txt
```

## 2. Run the tests

From the project root directory:

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=core --cov-report=term
```

## 3. Run specific tests

```bash
# Test a specific module
pytest core/tests/test_config_loader.py

# Test a specific class
pytest core/tests/test_logger.py::TestLogger

# Test a specific function
pytest core/tests/test_pdf_parser.py::TestPDFParser::test_extract_text
```

## That's it!

For more details, see:
- `TESTING.md` - Comprehensive testing guide
- `core/tests/README.md` - Detailed test documentation
- `.claude_docs/test_suite_documentation.md` - Implementation details

## Test Summary

✅ **10 test files** covering all core modules
✅ **150+ test functions** with comprehensive coverage
✅ **2,000+ lines** of test code
✅ **Mock fixtures** for external dependencies
✅ **Pytest configuration** ready to use

