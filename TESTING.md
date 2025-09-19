# Testing Guide

This document describes how to run tests for the ESO Top Builds project.

## Test Setup

Tests are located in the `tests/` directory and use pytest as the testing framework.

## Running Tests

### Install Test Dependencies

```bash
# Activate virtual environment
source venv/bin/activate

# Install pytest and other test dependencies
pip install pytest pytest-cov pytest-asyncio
```

### Run All Tests

```bash
# Run all tests
pytest

# Run tests with coverage report
pytest --cov=src/eso_builds

# Run tests with verbose output
pytest -v
```

### Run Specific Tests

```bash
# Run tests in a specific file
pytest tests/test_api.py

# Run a specific test function
pytest tests/test_api.py::test_fetch_encounters

# Run tests matching a pattern
pytest -k "api"
```

## Test Categories

### Unit Tests
- Test individual functions and classes
- Located in `tests/unit/`

### Integration Tests
- Test interactions with external APIs
- Located in `tests/integration/`
- May require API credentials

### End-to-End Tests
- Test complete workflows
- Located in `tests/e2e/`

## Writing Tests

When adding new features, please include:
1. Unit tests for core functionality
2. Integration tests for API interactions
3. Documentation of test scenarios

## Continuous Integration

Tests are automatically run on:
- Pull requests
- Commits to main branch

## Test Data

Test data and fixtures are stored in `tests/fixtures/`
