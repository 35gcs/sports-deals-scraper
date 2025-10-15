.PHONY: help bootstrap daily weekly test format lint clean install-browsers

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

bootstrap: install-browsers ## Bootstrap the project (install deps, browsers, setup)
	@echo "🚀 Bootstrapping sports deals scraper..."
	poetry install
	poetry run pre-commit install
	@echo "✅ Bootstrap complete! Run 'make daily' to fetch deals."

install-browsers: ## Install Playwright browsers
	@echo "📦 Installing Playwright browsers..."
	poetry run playwright install

daily: ## Run daily pipeline (fetch + rank)
	@echo "📊 Running daily pipeline..."
	poetry run deals fetch --sources all
	poetry run deals rank --min-discount 30
	@echo "✅ Daily pipeline complete! Check data/ directory for results."

weekly: ## Generate weekly digest
	@echo "📧 Generating weekly digest..."
	poetry run deals digest --week $(shell date +%Y-W%U) --top-per-sport 8
	@echo "✅ Weekly digest generated! Check out/ directory."

test: ## Run tests
	@echo "🧪 Running tests..."
	poetry run pytest

test-cov: ## Run tests with coverage
	@echo "🧪 Running tests with coverage..."
	poetry run pytest --cov=src --cov-report=html --cov-report=term-missing

format: ## Format code with black and ruff
	@echo "🎨 Formatting code..."
	poetry run black src tests
	poetry run ruff check --fix src tests

lint: ## Lint code
	@echo "🔍 Linting code..."
	poetry run ruff check src tests
	poetry run mypy src

validate: ## Run full validation (lint + test + type check)
	@echo "✅ Running full validation..."
	$(MAKE) lint
	$(MAKE) test
	poetry run deals validate

clean: ## Clean generated files
	@echo "🧹 Cleaning generated files..."
	rm -rf data/*.jsonl
	rm -rf out/*.html out/*.md
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

dev: ## Start development environment
	@echo "🛠️  Starting development environment..."
	poetry run pre-commit install
	@echo "✅ Development environment ready!"

# Data management
fetch-all: ## Fetch from all sources
	poetry run deals fetch --sources all

fetch-source: ## Fetch from specific source (usage: make fetch-source SOURCE=dicks)
	poetry run deals fetch --sources $(SOURCE)

rank-deals: ## Rank deals with minimum discount
	poetry run deals rank --min-discount 30

digest-week: ## Generate digest for specific week (usage: make digest-week WEEK=2025-W42)
	poetry run deals digest --week $(WEEK) --top-per-sport 8

# Database operations
init-db: ## Initialize database
	poetry run deals db init

reset-db: ## Reset database (WARNING: deletes all data)
	poetry run deals db reset

# Monitoring
logs: ## Show recent logs
	tail -f logs/deals.log

status: ## Show system status
	@echo "📊 System Status:"
	@echo "Database: $(shell poetry run deals db status)"
	@echo "Last fetch: $(shell poetry run deals db last-fetch)"
	@echo "Deal count: $(shell poetry run deals db count)"
