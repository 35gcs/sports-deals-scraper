# Youth Sports Gear Deals Scraper & Newsletter Generator

A production-ready system that collects best discounts on youth sports gear across reputable retailers, normalizes and ranks the deals, and outputs a ready-to-send weekly digest for parents.

## Features

- **Multi-retailer scraping**: Collects deals from 8+ major sports retailers
- **Smart normalization**: Maps products to unified schema with youth sizing detection
- **Intelligent ranking**: Scores deals by discount %, price, brand, and youth relevance
- **Deduplication**: Collapses identical items across retailers
- **Newsletter generation**: Creates responsive HTML and Markdown newsletters
- **Automated scheduling**: Daily fetch, weekly digest via GitHub Actions
- **Rate limiting**: Respects robots.txt and implements polite crawling
- **Schema validation**: Pydantic models ensure data quality

## Quick Start

### Prerequisites

- Python 3.11+
- Poetry (recommended) or pip

### Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd sports-deals-scraper

# Install dependencies
poetry install

# Install Playwright browsers
poetry run playwright install

# Set up pre-commit hooks
poetry run pre-commit install
```

### Configuration

Copy the example configuration and customize:

```bash
cp configs/sources.example.yaml configs/sources.yaml
```

Edit `configs/sources.yaml` to configure retailers, selectors, and rate limits.

### Running Locally

```bash
# Fetch deals from all sources
poetry run deals fetch --sources all

# Rank deals by score
poetry run deals rank --min-discount 30

# Generate weekly digest
poetry run deals digest --week 2025-W42 --top-per-sport 8

# Run validation and tests
poetry run deals validate
```

### Make Commands

```bash
# Bootstrap the project
make bootstrap

# Run daily pipeline
make daily

# Run weekly digest
make weekly

# Run tests
make test

# Format code
make format

# Lint code
make lint
```

## Project Structure

```
sports-deals-scraper/
├── src/
│   ├── collectors/          # Retailer-specific scrapers
│   ├── models.py           # Pydantic schemas
│   ├── ranker.py           # Scoring and ranking logic
│   ├── deduplicator.py     # Deal deduplication
│   ├── cli.py              # Command-line interface
│   └── utils/              # Common utilities
├── configs/
│   └── sources.yaml        # Retailer configurations
├── templates/
│   └── newsletter/         # Jinja2 templates
├── tests/
│   ├── fixtures/           # HTML fixtures for testing
│   └── test_*.py          # Test files
├── data/                   # Output data files
├── out/                    # Generated newsletters
└── .github/workflows/      # GitHub Actions
```

## Adding a New Retailer

1. Add configuration to `configs/sources.yaml`:

```yaml
retailers:
  - name: "New Retailer"
    base_url: "https://example.com/sale"
    selectors:
      item: ".product-card"
      title: ".product-title"
      price: ".price .sale"
      # ... other selectors
    sport: "soccer"
    youth_keywords: ["youth", "jr", "kids"]
```

2. Create a collector in `src/collectors/new_retailer.py`:

```python
from .base import BaseCollector

class NewRetailerCollector(BaseCollector):
    def parse_item(self, item_html: str) -> Deal:
        # Implementation here
        pass
```

3. Add tests in `tests/test_new_retailer.py`
4. Run validation: `poetry run deals validate`

## Newsletter Output

The system generates two newsletter formats:

- **HTML**: Responsive design with images, buttons, and styling
- **Markdown**: Plain text format for email platforms

Newsletters are organized by:
- Sport (soccer, basketball, hockey, etc.)
- Category (footwear, apparel, equipment, etc.)
- Age bands (youth, junior, kids)

## GitHub Actions

Two workflows are provided:

- **Daily fetch** (`daily.yml`): Runs at 13:05 ET to collect and rank deals
- **Weekly digest** (`weekly.yml`): Runs Thursdays at 10:00 ET to generate newsletter

## Data Schema

Each deal includes:

- Product details (title, brand, sport, category)
- Pricing (current price, MSRP, discount %)
- Youth detection (sizes, age bands)
- Retailer info (SKU, URL, stock status)
- Metadata (last seen, canonical URL)

## Rate Limiting & Compliance

- Respects `robots.txt` files
- Implements configurable rate limits per retailer
- Uses ETag/Last-Modified headers for caching
- Handles 429/5xx responses with backoff
- Only scrapes public product pages

## Testing

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=src

# Run specific test file
poetry run pytest tests/test_dicks.py

# Run with HTML fixtures
poetry run pytest tests/test_parsing.py
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Support

For issues and questions:
- Check the [Issues](https://github.com/your-repo/issues) page
- Review the configuration examples
- Run `poetry run deals validate` for diagnostics
