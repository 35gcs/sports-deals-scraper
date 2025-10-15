# Changelog

All notable changes to the Youth Sports Gear Deals Scraper will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial release of the Youth Sports Gear Deals Scraper
- Support for 8+ major sports retailers (Dick's, Academy, Scheels, Big 5, Nike, Adidas, Soccer.com, Monkey Sports)
- Comprehensive deal scoring and ranking system
- Deduplication across retailers using GTIN/MPN/SKU matching
- Newsletter generation with HTML and Markdown output
- CLI interface with fetch, rank, and digest commands
- GitHub Actions workflows for daily fetching and weekly newsletters
- Comprehensive test suite with fixtures and integration tests
- Rate limiting and polite crawling with robots.txt respect
- Youth detection algorithms for age-appropriate filtering
- Brand prestige scoring with sport-specific bonuses
- Price history tracking and validation
- Responsive newsletter templates with modern styling
- Database storage with SQLite and optional PostgreSQL support
- Configuration-driven retailer setup with YAML files
- Pre-commit hooks for code quality
- Make commands for common operations
- Detailed documentation and quick start guide

### Features
- **Multi-retailer scraping**: Collects deals from major sports retailers
- **Smart normalization**: Maps products to unified schema with youth sizing detection
- **Intelligent ranking**: Scores deals by discount %, price, brand, and youth relevance
- **Deduplication**: Collapses identical items across retailers
- **Newsletter generation**: Creates responsive HTML and Markdown newsletters
- **Automated scheduling**: Daily fetch, weekly digest via GitHub Actions
- **Rate limiting**: Respects robots.txt and implements polite crawling
- **Schema validation**: Pydantic models ensure data quality

### Technical Details
- **Language**: Python 3.11+
- **HTTP & Rendering**: Playwright (headless, stealth), httpx for API/RSS/JSON
- **Parsing**: selectolax for HTML; JSON-LD support
- **Data modeling**: Pydantic models for schemas and validation
- **Storage**: SQLite with dataset/sqlmodel; PostgreSQL support
- **Config**: YAML file for retailer configuration
- **CLI**: Typer with Rich for beautiful terminal output
- **Templates**: Jinja2 for newsletter generation
- **Testing**: pytest with fixtures and VCR.py for network cassettes
- **Quality**: Black, Ruff, MyPy for code quality
- **CI/CD**: GitHub Actions with automated workflows

### Retailers Supported
- Dick's Sporting Goods
- Academy Sports + Outdoors
- Scheels
- Big 5 Sporting Goods
- Nike
- Adidas
- Soccer.com
- HockeyMonkey
- BaseballMonkey
- LacrosseMonkey

### Sports Covered
- Soccer
- Basketball
- Hockey
- Lacrosse
- Tennis
- Baseball
- Softball
- Running
- Football
- Multi-sport

### Categories Supported
- Footwear
- Apparel
- Protective gear
- Equipment
- Bags
- Accessories

### CLI Commands
- `deals fetch` - Fetch deals from retailers
- `deals rank` - Rank deals by quality score
- `deals digest` - Generate weekly newsletter
- `deals validate` - Validate configuration and run tests
- `deals sources` - List configured sources
- `deals stats` - Show database statistics

### GitHub Actions
- **Daily fetch**: Runs at 1:05 PM ET to collect and rank deals
- **Weekly digest**: Runs Thursdays at 10:00 AM ET to generate newsletter
- **CI**: Runs tests on every push/PR

### Configuration
- YAML-based retailer configuration
- Rate limiting per retailer
- CSS selector customization
- Sport and category mapping
- Youth keyword detection
- Pagination support

### Newsletter Features
- Responsive HTML design
- Markdown export
- Grouped by sport and category
- Youth-focused filtering
- Deal scoring and ranking
- Coupon code display
- Stock status indicators
- Alternate retailer information

### Data Schema
- Comprehensive deal model with 20+ fields
- Price validation and discount calculation
- Youth detection and age range support
- Brand and sport classification
- Size and availability tracking
- Coupon and promotion support
- Deduplication and canonical URLs
- Timestamp and metadata tracking

### Testing
- Unit tests for all core functionality
- Integration tests for end-to-end workflows
- HTML fixtures for parser testing
- JSON-LD test data
- Mock data for development
- Coverage reporting
- VCR.py for network request recording

### Documentation
- Comprehensive README with setup instructions
- Quick start guide for new users
- Contributing guidelines for developers
- API documentation for all modules
- Configuration examples
- Troubleshooting guide
- Code examples and usage patterns

## [0.1.0] - 2025-01-XX

### Added
- Initial release
- Core scraping functionality
- Deal ranking and scoring
- Newsletter generation
- CLI interface
- GitHub Actions workflows
- Comprehensive test suite
- Documentation and examples

---

## Version History

- **0.1.0**: Initial release with core functionality
- **Unreleased**: Future features and improvements

## Roadmap

### Planned Features
- [ ] Additional retailer support
- [ ] Price history charts
- [ ] Web dashboard for deal management
- [ ] Discord/Slack notifications
- [ ] Email delivery integration
- [ ] Advanced filtering options
- [ ] Deal comparison tools
- [ ] Mobile app support
- [ ] API endpoints
- [ ] Advanced analytics

### Known Issues
- None at this time

### Deprecations
- None at this time

---

For more information, see the [README.md](README.md) and [CONTRIBUTING.md](CONTRIBUTING.md) files.
