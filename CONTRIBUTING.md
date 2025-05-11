# Contributing to Deep Deep Research v2

Thank you for considering contributing to Deep Deep Research v2! This document provides guidelines and instructions for contributing to this project.

## Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment for everyone. Please ensure that your interactions are professional and considerate.

## How to Contribute

### Reporting Issues

If you find a bug or want to suggest an enhancement:

1. Check if the issue already exists in the [GitHub Issues](https://github.com/yourusername/deep-deep-research-v2/issues)
2. If not, create a new issue with a clear title and detailed description
3. Include steps to reproduce the issue, expected behavior, and actual behavior
4. Add relevant screenshots or logs if applicable

### Pull Requests

1. Fork the repository
2. Create a new branch (`git checkout -b feature/your-feature-name`)
3. Make your changes
4. Run tests to ensure your changes don't break existing functionality
5. Commit your changes with clear commit messages following the convention:
   - `feat:` for new features
   - `fix:` for bug fixes
   - `docs:` for documentation
   - `style:` for formatting
   - `refactor:` for code refactoring
   - `test:` for adding tests
   - `chore:` for maintenance tasks
6. Push to your branch (`git push origin feature/your-feature-name`)
7. Open a Pull Request with a clear description of the changes

### Development Workflow

1. Set up the development environment as described in the README.md
2. Make sure all tests pass before making changes
3. Write tests for new features
4. Update documentation as needed
5. Follow the coding standards described below

## Coding Standards

### Python

- Follow PEP 8 conventions
- Use descriptive variable and function names
- Write docstrings for all functions, classes, and modules
- Keep functions focused on a single responsibility
- Maximum line length: 100 characters

### JavaScript (if applicable)

- Use ES6+ features when possible
- Follow the StandardJS style guide
- Add appropriate comments for complex logic

### Documentation

- Update relevant documentation when making changes
- Write clear and concise comments in code
- Use Markdown for documentation files

## Branching Strategy

- `main`: Production-ready code
- `develop`: Development branch where feature branches are merged
- `feature/*`: New features or enhancements
- `fix/*`: Bug fixes
- `docs/*`: Documentation updates
- `refactor/*`: Code refactoring without changing functionality

## Testing

- Write unit tests for all new features
- Ensure all tests pass before submitting a PR
- Aim for high test coverage

## Code Review Process

- All pull requests require at least one approval from a maintainer
- Address all review comments before merging
- Be respectful and constructive in code review discussions

Thank you for contributing to Deep Deep Research v2! 