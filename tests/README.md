# Cudy Scanner - Test Suite

This directory contains unit tests for the Cudy Scanner integration.

## Running Tests

### Prerequisites

Install test dependencies:

```bash
pip install pytest pytest-asyncio pytest-homeassistant-custom-component
```

### Run All Tests

```bash
pytest tests/
```

### Run Specific Test File

```bash
pytest tests/test_uptime_parsing.py
pytest tests/test_password_hashing.py
```

### Run with Coverage

```bash
pytest tests/ --cov=custom_components.cudy_scanner --cov-report=html
```

## Test Structure

- `test_uptime_parsing.py` - Tests for uptime string parsing to seconds
- `test_password_hashing.py` - Tests for password hashing algorithm

## Test Coverage Goals

- [x] Uptime parsing (all formats)
- [x] Password hashing (consistency, edge cases)
- [ ] Token extraction regex
- [ ] Error handling
- [ ] Integration tests (requires mock router)

## Writing New Tests

When adding new functionality, add corresponding tests:

1. Create test file: `tests/test_<feature>.py`
2. Follow existing test structure
3. Use descriptive test names
4. Test edge cases and error conditions
5. Update this README

## Notes

- Unit tests don't require Home Assistant to be running
- Integration tests will require mock router or test fixtures
- Some tests may need network access (marked with appropriate pytest markers)

