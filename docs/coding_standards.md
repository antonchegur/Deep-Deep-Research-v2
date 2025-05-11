# Deep Deep Research v2 - Coding Standards

This document outlines the coding standards, best practices, and code review processes for the Deep Deep Research v2 project.

## Code Style

### Python Style Guidelines

We follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) with some specific adaptations:

- **Line Length**: Maximum 100 characters (instead of PEP 8's 79)
- **Indentation**: 4 spaces (no tabs)
- **Quotes**: Prefer double quotes for strings with single quotes within them, single quotes otherwise
- **Docstrings**: Follow [Google style docstrings](https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html)
- **Imports**: Group imports in the following order, separated by a blank line:
  1. Standard library imports
  2. Related third-party imports
  3. Local application/library-specific imports

### Auto-Formatting Tools

To enforce consistent code style:

- **Black**: Use for automatic code formatting
- **isort**: Use for organizing imports
- **flake8**: Use for style guide enforcement

Configuration files for these tools are already in the repository root (.flake8, setup.cfg).

```bash
# Format code
make format

# Check style
make lint
```

## Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| Modules | lowercase, single word | `utils.py` |
| Packages | lowercase, single word | `research/` |
| Classes | CapWords/PascalCase | `WikipediaAdapter` |
| Functions/Methods | snake_case | `process_text()` |
| Variables | snake_case | `source_count` |
| Constants | UPPERCASE_WITH_UNDERSCORES | `MAX_SOURCES` |
| Private Methods/Variables | Prefix with underscore | `_internal_method()` |
| Type Aliases | CapWords/PascalCase | `SourceType` |

### Special Naming Guidelines

- **Avoid Single-Character Names**: Except for counters in short loops
- **Avoid Abbreviations**: Unless very common (e.g., `http`, `pdf`)
- **Boolean Variables**: Prefix with `is_`, `has_`, or similar
- **File Names**: Reflect their primary class/function, e.g., `wikipedia_adapter.py`

## Documentation Standards

### Code Documentation

- **Module Header**: Include a docstring at the top of each module explaining its purpose
- **Class Docstrings**: Explain the class purpose, attributes, and behavior
- **Function Docstrings**: Document parameters, return values, exceptions, and behavior
- **Complex Logic**: Add inline comments for non-obvious logic

Example:

```python
"""
Wikipedia data adapter for retrieving and processing Wikipedia articles.
"""

from typing import Dict, List, Optional


class WikipediaAdapter:
    """
    Adapter for interfacing with Wikipedia API and processing articles.
    
    This class manages connection to Wikipedia, search functionality,
    and content extraction with proper handling of rate limits.
    """
    
    def get_article_content(self, title: str, language: str = "en") -> Optional[Dict]:
        """
        Retrieve the full content of a Wikipedia article.
        
        Args:
            title: The title of the Wikipedia article
            language: The language code (default: "en" for English)
            
        Returns:
            Dictionary containing article text, sections, and metadata
            or None if the article doesn't exist
            
        Raises:
            ConnectionError: If Wikipedia API is unavailable
            RateLimitError: If rate limit is exceeded
        """
        # Implementation here
```

### Project Documentation

- **README.md**: Overview, installation, basic usage
- **Architecture Documentation**: In `docs/architecture.md`
- **API Documentation**: Generated from docstrings using pdoc3
- **User Guide**: In `docs/user_guide.md` (as the project matures)

Generate API documentation with:

```bash
pdoc3 --html --output-dir docs/api src/
```

## Testing Standards

### Test Requirements

- **Coverage Target**: Minimum 80% code coverage
- **Test Types Required**:
  - Unit Tests: For all modules
  - Integration Tests: For all service integrations
  - End-to-End Tests: For main workflows

### Test Structure

- Use pytest as the testing framework
- Test files should mirror the module structure: `test_<module_name>.py`
- Use fixtures for test setup
- Use parametrization for testing multiple inputs
- Use mocks to isolate units

Example:

```python
import pytest
from src.research.wikipedia_adapter import WikipediaAdapter


@pytest.fixture
def wikipedia_adapter():
    return WikipediaAdapter()


def test_article_retrieval(wikipedia_adapter, mock_wikipedia_api):
    # Test implementation
    result = wikipedia_adapter.get_article_content("Python (programming language)")
    assert result["title"] == "Python (programming language)"
    assert "sections" in result


@pytest.mark.parametrize("language", ["en", "ru", "es", "kk"])
def test_multilingual_support(wikipedia_adapter, language):
    # Test implementation
```

### Running Tests

```bash
# Run all tests
make test

# Run with coverage report
pytest --cov=src
```

## Code Review Process

### Pull Request Guidelines

- **Title Format**: `<type>: <description>` (e.g., "feat: Add Wikipedia integration")
- **Types**:
  - `feat`: New feature
  - `fix`: Bug fix
  - `docs`: Documentation only
  - `style`: Formatting, missing semicolons, etc.
  - `refactor`: Code change that neither fixes a bug nor adds a feature
  - `perf`: Code change that improves performance
  - `test`: Adding tests
  - `chore`: Changes to the build process or auxiliary tools

- **PR Description**: Include:
  - Purpose of changes
  - Issue number (if applicable)
  - Testing done
  - Screenshots (if UI changes)

### Review Process

1. **Author**: Create PR with proper description
2. **Reviewers**: At least one team member must review
3. **Check**:
   - Code style compliance
   - Test coverage
   - Documentation completeness
   - Implementation quality
4. **Feedback**: Provide specific, constructive feedback
5. **Updates**: Author addresses feedback
6. **Approval**: Reviewer approves when satisfied
7. **Merge**: Author merges once approved

### Code Review Checklist

- Does the code follow our style guidelines?
- Are there adequate tests?
- Is the documentation complete?
- Is the code efficient and maintainable?
- Are there any security concerns?
- Is error handling appropriate?
- Is logging sufficient?

## Error Handling and Logging

### Error Handling Principles

- Be specific with exception types
- Handle exceptions at the appropriate level
- Log meaningful error messages
- Fail early and explicitly
- Provide helpful user-facing error messages

### Logging Standards

- Use the built-in `logging` module
- Log levels:
  - DEBUG: Detailed information for debugging
  - INFO: Confirmation of expected events
  - WARNING: Unexpected but non-critical issues
  - ERROR: Errors that prevent functionality
  - CRITICAL: System-wide failures

Example:

```python
import logging

logger = logging.getLogger(__name__)

def process_research_data(data):
    try:
        result = transform_data(data)
        logger.info("Successfully processed %d items", len(data))
        return result
    except ValueError as e:
        logger.error("Data validation error: %s", str(e))
        raise
    except Exception as e:
        logger.critical("Unexpected error in data processing: %s", str(e), exc_info=True)
        raise
```

## Version Control Guidelines

### Commit Message Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

- **Type**: feat, fix, docs, style, refactor, perf, test, chore
- **Scope**: Component affected (e.g., api, pdf, data)
- **Subject**: Brief description in present tense
- **Body**: Detailed explanation if needed
- **Footer**: Breaking changes, issue references

Example:
```
feat(research): Implement Wikipedia data extraction

Add Wikipedia adapter with search and content retrieval functions.
Includes rate limiting and error handling.

Closes #42
```

### Branching Strategy

- `main`: Production-ready code
- `develop`: Development branch, relatively stable
- Feature branches: `feature/<feature-name>`
- Bug fix branches: `fix/<bug-description>`
- Release branches: `release/<version>`

## Security Best Practices

- Use `python-dotenv` for environment variables
- Never commit API keys or credentials
- Validate all user inputs
- Use proper HTTP methods and status codes
- Sanitize data before processing
- Follow the principle of least privilege

## Performance Considerations

- Profile code for bottlenecks
- Use async where appropriate for I/O operations
- Implement caching for expensive operations
- Batch API requests when possible
- Use pagination for large datasets
- Consider memory usage with large documents

## Accessibility Standards

- Support multilingual output
- Provide alternative text for images in reports
- Ensure PDF reports meet basic accessibility standards
- Use sufficient color contrast in visualizations
- Include metadata in generated documents

## Continuous Improvement

These standards should evolve as the project grows. Team members are encouraged to suggest improvements by opening issues or pull requests for this document. 