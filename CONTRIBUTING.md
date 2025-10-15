# Contributing to Sports Deals Scraper

Thank you for your interest in contributing to the Youth Sports Gear Deals Scraper! This document provides guidelines and information for contributors.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally
3. **Set up the development environment**:
   ```bash
   git clone https://github.com/your-username/sports-deals-scraper.git
   cd sports-deals-scraper
   poetry install
   poetry run playwright install
   poetry run pre-commit install
   ```

## Development Setup

### Prerequisites
- Python 3.11+
- Poetry
- Git

### Environment Setup
```bash
# Install dependencies
poetry install

# Install development dependencies
poetry install --with dev

# Install pre-commit hooks
poetry run pre-commit install

# Install Playwright browsers
poetry run playwright install
```

### Running Tests
```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=src --cov-report=html

# Run specific test file
poetry run pytest tests/test_models.py

# Run with verbose output
poetry run pytest -v
```

### Code Quality
```bash
# Format code
poetry run black src tests

# Lint code
poetry run ruff check src tests

# Type checking
poetry run mypy src

# Run all quality checks
make lint
```

## Contributing Guidelines

### Code Style
- Follow PEP 8 style guidelines
- Use Black for code formatting
- Use Ruff for linting
- Use MyPy for type checking
- Write docstrings for all public functions and classes

### Commit Messages
Use clear, descriptive commit messages:
```
feat: add new retailer collector for Target
fix: resolve rate limiting issue in Academy collector
docs: update README with new installation steps
test: add tests for deduplication logic
```

### Pull Request Process
1. **Create a feature branch** from `main`
2. **Make your changes** with appropriate tests
3. **Run tests** to ensure everything passes
4. **Update documentation** if needed
5. **Submit a pull request** with a clear description

## Adding New Retailers

### 1. Create Collector Class
Create a new file in `src/collectors/` (e.g., `target.py`):

```python
from .base import BaseCollector
from ..models import Deal, Sport, Category

class TargetCollector(BaseCollector):
    """Collector for Target deals."""
    
    def _parse_item_specific(self, item_html: str, deal_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Target-specific data."""
        # Implementation here
        pass
    
    async def collect_deals(self) -> List[Deal]:
        """Collect deals from Target."""
        return await self.collect_deals_with_pagination()
```

### 2. Update Configuration
Add retailer configuration to `configs/sources.yaml`:

```yaml
- name: "Target"
  base_url: "https://www.target.com/c/sports-outdoors/-/N-5xtg6"
  enabled: true
  requires_js: true
  selectors:
    item: ".product-card"
    title: ".product-title"
    price: ".price .sale-price"
    # ... other selectors
  sport: "multi"
  youth_keywords: ["youth", "jr", "kids"]
  rate_limit:
    requests_per_minute: 8
    burst: 2
```

### 3. Add Tests
Create test file `tests/test_target.py`:

```python
import pytest
from src.collectors.target import TargetCollector

def test_target_collector():
    """Test Target collector functionality."""
    # Test implementation
    pass
```

### 4. Update Imports
Add the new collector to `src/collectors/__init__.py`:

```python
from .target import TargetCollector

__all__ = [
    # ... existing collectors
    "TargetCollector",
]
```

## Adding New Features

### 1. Scoring Algorithms
To add new scoring criteria:

1. **Add function** in `src/utils/scoring.py`
2. **Update composite score** calculation
3. **Add tests** for the new scoring logic
4. **Update documentation** with scoring details

### 2. Newsletter Templates
To customize newsletter output:

1. **Modify templates** in `templates/newsletter/`
2. **Add new template variables** in `src/newsletter.py`
3. **Test template rendering** with sample data
4. **Update documentation** with template usage

### 3. Data Models
To extend data models:

1. **Update models** in `src/models.py`
2. **Add validation** for new fields
3. **Update serialization** logic
4. **Add migration** for existing data
5. **Update tests** to cover new fields

## Testing Guidelines

### Test Structure
- **Unit tests**: Test individual functions and classes
- **Integration tests**: Test component interactions
- **End-to-end tests**: Test complete workflows

### Test Data
- Use **fixtures** for common test data
- Create **realistic test cases** with actual HTML samples
- **Mock external dependencies** (HTTP requests, databases)

### Test Coverage
- Aim for **80%+ code coverage**
- Test **edge cases** and error conditions
- Test **validation logic** thoroughly

## Documentation

### Code Documentation
- **Docstrings**: Use Google-style docstrings
- **Type hints**: Add type annotations for all functions
- **Comments**: Explain complex logic and business rules

### User Documentation
- **README.md**: Keep installation and usage instructions current
- **QUICKSTART.md**: Provide quick start guide for new users
- **API docs**: Document public APIs and configuration options

## Issue Reporting

### Bug Reports
When reporting bugs, include:
- **Description** of the issue
- **Steps to reproduce** the problem
- **Expected behavior** vs actual behavior
- **Environment details** (OS, Python version, etc.)
- **Error messages** and logs

### Feature Requests
When requesting features, include:
- **Use case** and motivation
- **Proposed solution** or approach
- **Alternative solutions** considered
- **Additional context** or examples

## Release Process

### Versioning
We use [Semantic Versioning](https://semver.org/):
- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Release Checklist
- [ ] All tests pass
- [ ] Documentation updated
- [ ] Version bumped in `pyproject.toml`
- [ ] CHANGELOG.md updated
- [ ] GitHub release created
- [ ] PyPI package published (if applicable)

## Community Guidelines

### Code of Conduct
- Be respectful and inclusive
- Focus on constructive feedback
- Help others learn and grow
- Follow the project's coding standards

### Getting Help
- **GitHub Issues**: For bugs and feature requests
- **Discussions**: For questions and general discussion
- **Pull Requests**: For code contributions

## License

By contributing to this project, you agree that your contributions will be licensed under the same license as the project (MIT License).

## Recognition

Contributors will be recognized in:
- **README.md** contributors section
- **GitHub** contributor statistics
- **Release notes** for significant contributions

Thank you for contributing to the Youth Sports Gear Deals Scraper! 🏈⚽🏀
