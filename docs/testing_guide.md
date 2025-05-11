# Deep Deep Research v2 Testing Guide

This guide outlines the testing approach, patterns, and best practices for the Deep Deep Research v2 project. It serves as a reference for all contributors to ensure consistent and effective testing across the codebase.

## Testing Framework

Deep Deep Research v2 uses pytest as its primary testing framework, with additional tools and extensions:

- **pytest**: Core testing framework
- **pytest-cov**: For measuring test coverage
- **pytest-asyncio**: For testing asynchronous code
- **unittest.mock**: For mocking dependencies
- **tox**: For testing in multiple environments

## Test Directory Structure

The test directory is organized as follows:

```
tests/
├── conftest.py             # Shared pytest fixtures
├── test_helpers.py         # Helper functions for tests
├── test_*.py               # Unit tests for specific modules
├── chunking/               # Tests for chunking module
├── research/               # Tests for research module
└── test_data/              # Test data files
```

## Test Types

### 1. Unit Tests

Unit tests verify the behavior of individual functions, methods, or classes in isolation. They should be fast, self-contained, and not depend on external resources.

Example:
```python
def test_text_processor_clean_text():
    processor = TextProcessor()
    result = processor.clean_text("Test  with extra  spaces")
    assert result == "Test with extra spaces"
```

### 2. Integration Tests

Integration tests verify that multiple components work together correctly. They may need more setup and may test interactions with external dependencies (often mocked).

Example:
```python
def test_research_pipeline_integration(mock_source_manager, mock_synthesizer):
    pipeline = ResearchPipeline(source_manager=mock_source_manager, synthesizer=mock_synthesizer)
    # Configure mocks
    mock_source_manager.search.return_value = [...]
    # Test the integration
    result = pipeline.research("test query")
    assert result["status"] == "success"
    # Verify interactions
    mock_source_manager.search.assert_called_once_with("test query")
```

### 3. End-to-End Tests

End-to-end tests verify complete user workflows from input to output. They may involve actual external services (though prefer to mock these when possible).

Example:
```python
def test_end_to_end_research_flow(sample_research_topic, temp_dir):
    # Set up a complete test environment
    output_file = temp_dir / "output.pdf"
    result = run_research_pipeline(sample_research_topic, output_file)
    # Verify results
    assert result["status"] == "success"
    assert output_file.exists()
    assert output_file.stat().st_size > 0
```

### 4. Performance Tests

Performance tests verify that the system meets performance requirements. They measure execution time, memory usage, or other performance metrics.

Example:
```python
def test_chunking_performance(large_test_document):
    start_time = time.time()
    chunks = chunk_document(large_test_document)
    end_time = time.time()
    
    # Verify performance
    assert end_time - start_time < 2.0  # Should chunk in under 2 seconds
    assert len(chunks) > 0
```

## Test Fixtures

Fixtures provide reusable test data and setup. Define fixtures in `conftest.py` for global access or in test modules for local use.

```python
@pytest.fixture
def sample_text_content():
    """Fixture that provides sample text content for chunking and processing tests"""
    return """
    Deep Deep Research v2 is an advanced research tool that leverages AI to perform
    comprehensive research on any topic. It integrates with multiple data sources,
    processes and synthesizes information, and generates detailed reports.
    """
```

## Test Helpers

The `test_helpers.py` module provides utility functions and classes to standardize common testing patterns:

- `compare_json_data()`: Compare JSON objects and report differences
- `save_test_output()`: Save test output to a file for debugging
- `async_test()`: Decorator for testing async functions
- `MockResponse`: Mock HTTP responses for API testing
- `ParameterizedTestCase`: Helper for parameterized tests
- `assert_files_equal()`: Compare files for equality
- And more...

## Best Practices

### 1. Test Naming and Organization

- Name test functions with `test_` prefix
- Use descriptive names that indicate what's being tested
- Group related tests in classes or modules
- Organize tests to mirror the structure of the code being tested

### 2. Isolation and Independence

- Each test should be independent of others
- Clean up after tests that create resources (files, database entries, etc.)
- Use fixtures to set up and tear down test environments
- Avoid tests that depend on the order of execution

### 3. Mocking and Test Doubles

- Use mocks to isolate the code under test from its dependencies
- Prefer mocking at boundaries between your code and external systems
- Don't mock the code under test itself
- Configure mocks to return realistic, relevant data

### 4. Assertions and Verification

- Use specific, clear assertions
- Test both expected success cases and error handling
- Verify not just return values but also side effects
- Use soft assertions for multiple checks in a single test

### 5. Test Coverage

- Aim for high test coverage, but don't sacrifice quality for quantity
- Focus on testing business logic and edge cases
- Use coverage reports to identify untested code
- Write tests for bugs before fixing them

### 6. Parameterized Tests

Use parameterized tests to run the same test with different inputs:

```python
@pytest.mark.parametrize("input_text,expected", [
    ("test", "TEST"),
    ("hello", "HELLO"),
    ("", ""),
])
def test_to_uppercase(input_text, expected):
    assert to_uppercase(input_text) == expected
```

### 7. Testing Asynchronous Code

Use pytest-asyncio to test async functions:

```python
@pytest.mark.asyncio
async def test_async_function():
    result = await async_function()
    assert result == expected
```

Or use the `async_test` decorator:

```python
@async_test
async def test_async_function():
    result = await async_function()
    assert result == expected
```

## Running Tests

### Basic Test Execution

```bash
# Run all tests
pytest

# Run tests in a specific file
pytest tests/test_research_pipeline.py

# Run a specific test
pytest tests/test_research_pipeline.py::test_research_flow
```

### Test Options

```bash
# Run tests with output
pytest -v

# Run tests and show coverage
pytest --cov=src

# Generate HTML coverage report
pytest --cov=src --cov-report=html

# Run only tests marked with a specific marker
pytest -m "slow"
```

### Using Tox

Tox automates testing in multiple environments:

```bash
# Run tests in all configured environments
tox

# Run tests in a specific environment
tox -e py39
```

## Test Resources

### Test Data

- Place test data files in the `tests/test_data` directory
- Use the `get_test_data_path()` helper to locate test data files
- Keep test data small and focused

### External Resources

- Prefer mocking external resources in tests
- If you must use real external resources, make it configurable
- Consider using Docker for more complex external dependencies

## Troubleshooting Tests

### Tests Running Slowly

- Look for tests that access external resources without mocking
- Consider using the `--durations=10` flag to identify slow tests
- Mark slow tests with `@pytest.mark.slow` and exclude them from regular runs

### Flaky Tests

- Identify and fix tests that fail intermittently
- Common causes: timing issues, order dependencies, shared state
- Add proper cleanup to tests that modify global state

### Debugging Failed Tests

- Use `pytest -v` for more detailed output
- Use `pytest --pdb` to drop into the debugger on failure
- Add print statements with `pytest -s` to see output

## Continuous Integration

The CI pipeline runs tests on every push and pull request:

- All tests must pass before code can be merged
- Coverage reports are generated and tracked
- Performance regression tests are run on scheduled basis

## Documentation

- Document test strategies for complex components
- Explain test data and fixtures in docstrings
- Keep test code clean and readable - it serves as documentation
- Update this guide when introducing new testing patterns or tools 