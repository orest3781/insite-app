# Contributing to InSite App

Thank you for considering contributing to InSite App! 🎉

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
- [Development Setup](#development-setup)
- [Coding Standards](#coding-standards)
- [Commit Guidelines](#commit-guidelines)
- [Pull Request Process](#pull-request-process)

---

## Code of Conduct

This project follows a simple code of conduct:
- Be respectful and inclusive
- Welcome newcomers
- Focus on what's best for the project
- Show empathy towards others

---

## How Can I Contribute?

### 🐛 Reporting Bugs

Before creating bug reports, please check existing issues. When creating a bug report, include:

- **Clear title and description**
- **Steps to reproduce**
- **Expected vs actual behavior**
- **System information** (OS, Python version)
- **Log files** (if applicable)

### 💡 Suggesting Features

Feature requests are welcome! Please:
- Use a clear and descriptive title
- Provide detailed description of the feature
- Explain why this feature would be useful
- Include mockups or examples if possible

### 🔨 Code Contributions

1. **Fork the repository**
2. **Create a feature branch** (`git checkout -b feature/amazing-feature`)
3. **Make your changes**
4. **Test thoroughly**
5. **Commit your changes** (see commit guidelines below)
6. **Push to your fork** (`git push origin feature/amazing-feature`)
7. **Open a Pull Request**

---

## Development Setup

### Prerequisites

- Python 3.11 or higher
- Git
- Tesseract OCR (for testing OCR features)
- Poppler (for PDF support)
- Ollama (optional, for AI features)

### Setup Steps

```powershell
# Clone your fork
git clone https://github.com/YOUR_USERNAME/insite-app.git
cd insite-app

# Create virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Initialize database
python init_database.py

# Run application
python main.py
```

### Running Tests

```powershell
# Run all tests
pytest tests/

# Run specific test
pytest tests/test_database.py

# Run with coverage
pytest --cov=src tests/
```

---

## Coding Standards

### Python Style Guide

We follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) with some modifications:

- **Line length:** 100 characters (not 79)
- **Indentation:** 4 spaces
- **Quotes:** Double quotes for strings
- **Imports:** Grouped and sorted (stdlib, third-party, local)

### Code Quality

- **Type hints:** Use type hints for function signatures
- **Docstrings:** Use Google-style docstrings
- **Logging:** Use the logging framework, not print()
- **Error handling:** Handle exceptions appropriately
- **Comments:** Write clear comments for complex logic

### Example

```python
from typing import Optional, List
from pathlib import Path

def process_file(file_path: Path, options: Optional[dict] = None) -> List[str]:
    """
    Process a file and return extracted text.
    
    Args:
        file_path: Path to the file to process
        options: Optional processing options
        
    Returns:
        List of extracted text lines
        
    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file format is unsupported
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    # Implementation...
    return []
```

---

## Commit Guidelines

### Commit Message Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- **feat:** New feature
- **fix:** Bug fix
- **docs:** Documentation only
- **style:** Code style changes (formatting, no logic change)
- **refactor:** Code refactoring
- **perf:** Performance improvement
- **test:** Adding or updating tests
- **chore:** Maintenance tasks

### Examples

```
feat(ocr): Add support for multi-column layout detection

Implement column detection algorithm to improve OCR accuracy
for documents with multiple columns.

Closes #123
```

```
fix(database): Resolve foreign key constraint violation

Fixed issue where orphaned records caused integrity errors
when deleting files.

Fixes #456
```

### Rules

- Use present tense ("Add feature" not "Added feature")
- Use imperative mood ("Move cursor to..." not "Moves cursor to...")
- First line max 72 characters
- Reference issues and PRs in footer

---

## Pull Request Process

### Before Submitting

- [ ] Run all tests and ensure they pass
- [ ] Update documentation if needed
- [ ] Add tests for new features
- [ ] Follow coding standards
- [ ] Update CHANGELOG.md (if applicable)

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
Describe testing performed

## Screenshots (if applicable)
Add screenshots for UI changes

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-reviewed code
- [ ] Commented complex code
- [ ] Updated documentation
- [ ] No new warnings
- [ ] Added tests
- [ ] All tests pass
```

### Review Process

1. **Automated checks** must pass (if CI/CD is set up)
2. **Code review** by maintainer(s)
3. **Testing** on different platforms (if applicable)
4. **Approval** and merge

---

## Project Structure

```
insite-app/
├── src/                    # Source code
│   ├── core/              # Core services
│   ├── models/            # Database models
│   ├── processing/        # Processing logic
│   ├── ui/                # UI components
│   └── utils/             # Utilities
├── tests/                 # Test files
├── docs/                  # Documentation
├── config/                # Configuration
└── data/                  # Runtime data (not in git)
```

---

## Documentation

### Updating Documentation

- Update relevant `.md` files in `/docs`
- Update docstrings in code
- Update README.md if needed
- Add examples for new features

### Documentation Standards

- Use Markdown format
- Include code examples
- Add screenshots for UI features
- Keep it up-to-date

---

## Areas for Contribution

### Priority Areas

1. **Testing:** Increase test coverage
2. **Documentation:** Improve user guides and API docs
3. **Performance:** Optimize processing speed
4. **UI/UX:** Enhance user interface
5. **Platform support:** Linux/macOS compatibility

### Good First Issues

Look for issues labeled `good first issue` or `help wanted` in the issue tracker.

---

## Questions?

- **GitHub Issues:** Open an issue for questions
- **Discussions:** Use GitHub Discussions for general questions
- **Email:** Contact maintainers (if provided)

---

## Recognition

Contributors will be:
- Listed in CONTRIBUTORS.md
- Mentioned in release notes
- Credited in commit history

---

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to InSite App! 🚀
