# Quick Start Guide

Get up and running with the Youth Sports Gear Deals Scraper in minutes!

## Prerequisites

- Python 3.11+
- Poetry (recommended) or pip

## Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd sports-deals-scraper
   ```

2. **Install dependencies**
   ```bash
   poetry install
   ```

3. **Install Playwright browsers**
   ```bash
   poetry run playwright install
   ```

4. **Set up configuration**
   ```bash
   cp configs/sources.example.yaml configs/sources.yaml
   ```

## Quick Commands

### Fetch Deals
```bash
# Fetch from all sources
poetry run deals fetch --sources all

# Fetch from specific sources
poetry run deals fetch --sources "dicks,academy"

# Fetch with filters
poetry run deals fetch --min-discount 30 --youth-only --max-deals 100
```

### Rank Deals
```bash
# Rank deals by quality score
poetry run deals rank --min-discount 30 --limit 50

# Rank youth deals only
poetry run deals rank --youth-only --limit 20
```

### Generate Newsletter
```bash
# Generate weekly digest
poetry run deals digest --week 2025-W01 --top-per-sport 8

# Generate with custom settings
poetry run deals digest --min-discount 25 --youth-only --formats "html,markdown"
```

### Validate Setup
```bash
# Check configuration and run tests
poetry run deals validate

# List configured sources
poetry run deals sources

# Show database statistics
poetry run deals stats
```

## Make Commands

For convenience, use the provided Make commands:

```bash
# Bootstrap the project
make bootstrap

# Run daily pipeline (fetch + rank)
make daily

# Generate weekly digest
make weekly

# Run tests
make test

# Format and lint code
make format
make lint
```

## Configuration

Edit `configs/sources.yaml` to customize:

- **Retailers**: Add/remove retailers, modify URLs
- **Selectors**: Update CSS selectors for data extraction
- **Rate Limits**: Adjust request rates per retailer
- **Sports/Categories**: Configure sport and category mappings

## Output Files

- **Data**: `data/deals-YYYY-MM-DD.jsonl` - Raw deals data
- **Ranked**: `data/top-deals-YYYY-MM-DD.jsonl` - Ranked deals
- **Newsletter**: `out/digest-YYYY-WW.html` - HTML newsletter
- **Newsletter**: `out/digest-YYYY-WW.md` - Markdown newsletter

## GitHub Actions

The project includes automated workflows:

- **Daily**: Fetches deals every day at 1:05 PM ET
- **Weekly**: Generates newsletter every Thursday at 10:00 AM ET
- **CI**: Runs tests on every push/PR

## Troubleshooting

### Common Issues

1. **Playwright browser not found**
   ```bash
   poetry run playwright install
   ```

2. **Configuration errors**
   ```bash
   poetry run deals validate
   ```

3. **No deals found**
   - Check if retailers are enabled in config
   - Verify selectors are correct
   - Check rate limits

4. **Rate limiting errors**
   - Increase delays in configuration
   - Reduce concurrent requests

### Getting Help

- Check the [README.md](README.md) for detailed documentation
- Review the [tests](tests/) for usage examples
- Open an issue for bugs or feature requests

## Next Steps

1. **Customize Configuration**: Edit `configs/sources.yaml` for your needs
2. **Add Retailers**: Create new collector classes for additional retailers
3. **Modify Templates**: Customize newsletter templates in `templates/`
4. **Set Up Automation**: Configure GitHub Actions for your repository
5. **Monitor Results**: Check the generated newsletters and adjust settings

## Example Workflow

```bash
# 1. Bootstrap the project
make bootstrap

# 2. Fetch deals from all sources
poetry run deals fetch --sources all --output data/deals-$(date +%Y-%m-%d).jsonl

# 3. Rank deals by quality
poetry run deals rank --min-discount 30 --output data/top-deals-$(date +%Y-%m-%d).jsonl

# 4. Generate newsletter
poetry run deals digest --week $(date +%Y-W%U) --top-per-sport 8

# 5. Check results
ls -la out/
ls -la data/
```

That's it! You're now ready to start collecting and ranking youth sports gear deals.
