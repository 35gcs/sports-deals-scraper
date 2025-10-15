"""Command-line interface for the sports deals scraper."""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from .collectors import (
    DicksCollector,
    AcademyCollector,
    ScheelsCollector,
    Big5Collector,
    NikeCollector,
    AdidasCollector,
    SoccerComCollector,
    MonkeySportsCollector,
)
from .database import get_database
from .deduplicator import DealDeduplicator
from .models import Deal, NewsletterConfig, RetailerConfig
from .newsletter import NewsletterGenerator
from .ranker import DealRanker
from .utils.validation import validate_retailer_config

app = typer.Typer(help="Youth Sports Gear Deals Scraper & Newsletter Generator")
console = Console()

# Global configuration
CONFIG_FILE = Path("configs/sources.yaml")
OUTPUT_DIR = Path("out")
DATA_DIR = Path("data")


@app.command()
def fetch(
    sources: str = typer.Option("all", help="Sources to fetch from (comma-separated or 'all')"),
    output: Optional[str] = typer.Option(None, help="Output file for deals (JSON Lines format)"),
    min_discount: float = typer.Option(0.0, help="Minimum discount percentage to include"),
    youth_only: bool = typer.Option(False, help="Only fetch youth items"),
    max_deals: int = typer.Option(0, help="Maximum number of deals to fetch (0 = no limit)"),
):
    """Fetch deals from configured retailers."""
    console.print(f"🚀 Fetching deals from sources: {sources}")
    
    # Load configuration
    configs = _load_retailer_configs()
    if not configs:
        console.print("❌ No retailer configurations found", style="red")
        raise typer.Exit(1)
    
    # Filter sources
    if sources.lower() != "all":
        source_names = [s.strip() for s in sources.split(",")]
        configs = [c for c in configs if c.name.lower() in [s.lower() for s in source_names]]
    
    if not configs:
        console.print("❌ No matching sources found", style="red")
        raise typer.Exit(1)
    
    # Fetch deals
    all_deals = asyncio.run(_fetch_deals_from_sources(configs))
    
    # Filter deals
    filtered_deals = _filter_deals(all_deals, min_discount, youth_only, max_deals)
    
    # Save to database
    db = get_database()
    saved_count = db.save_deals(filtered_deals)
    console.print(f"💾 Saved {saved_count} deals to database")
    
    # Save to file if specified
    if output:
        output_path = Path(output)
        _save_deals_to_file(filtered_deals, output_path)
        console.print(f"📁 Saved {len(filtered_deals)} deals to {output_path}")
    
    # Show summary
    _show_fetch_summary(filtered_deals, configs)


@app.command()
def rank(
    min_discount: float = typer.Option(30.0, help="Minimum discount percentage to include"),
    youth_only: bool = typer.Option(False, help="Only rank youth items"),
    limit: int = typer.Option(50, help="Maximum number of deals to return"),
    output: Optional[str] = typer.Option(None, help="Output file for ranked deals"),
):
    """Rank deals by quality score."""
    console.print("📊 Ranking deals by quality score...")
    
    # Get deals from database
    db = get_database()
    deals = db.get_deals(min_discount=min_discount, youth_only=youth_only)
    
    if not deals:
        console.print("❌ No deals found in database", style="red")
        raise typer.Exit(1)
    
    # Rank deals
    ranker = DealRanker(min_discount=min_discount)
    ranked_deals = ranker.get_top_deals(deals, limit)
    
    # Save to file if specified
    if output:
        output_path = Path(output)
        _save_deals_to_file(ranked_deals, output_path)
        console.print(f"📁 Saved {len(ranked_deals)} ranked deals to {output_path}")
    
    # Show ranking summary
    _show_ranking_summary(ranked_deals)


@app.command()
def digest(
    week: str = typer.Option(None, help="Week identifier (e.g., 2025-W42)"),
    top_per_sport: int = typer.Option(8, help="Top deals per sport"),
    min_discount: float = typer.Option(20.0, help="Minimum discount percentage"),
    youth_only: bool = typer.Option(True, help="Only include youth items"),
    formats: str = typer.Option("html,markdown", help="Output formats (comma-separated)"),
    output_dir: str = typer.Option("out", help="Output directory"),
):
    """Generate weekly newsletter digest."""
    if not week:
        week = datetime.now().strftime("%Y-W%U")
    
    console.print(f"📧 Generating newsletter for week {week}")
    
    # Get deals from database
    db = get_database()
    deals = db.get_deals(min_discount=min_discount, youth_only=youth_only)
    
    if not deals:
        console.print("❌ No deals found in database", style="red")
        raise typer.Exit(1)
    
    # Configure newsletter
    newsletter_config = NewsletterConfig(
        top_per_sport=top_per_sport,
        min_discount_pct=min_discount,
        show_youth_only=youth_only,
        formats=[f.strip() for f in formats.split(",")],
        output_dir=output_dir,
    )
    
    # Generate newsletter
    generator = NewsletterGenerator(newsletter_config)
    newsletters = generator.generate_newsletter(deals, week)
    
    # Save newsletters
    saved_files = generator.save_newsletter(newsletters, week)
    
    console.print(f"✅ Generated newsletter in {len(saved_files)} formats:")
    for format_name, filepath in saved_files.items():
        console.print(f"  📄 {format_name.upper()}: {filepath}")


@app.command()
def validate():
    """Validate configuration and run tests."""
    console.print("🔍 Validating configuration and running tests...")
    
    # Load and validate configurations
    configs = _load_retailer_configs()
    if not configs:
        console.print("❌ No retailer configurations found", style="red")
        raise typer.Exit(1)
    
    # Validate each configuration
    validation_errors = []
    for config in configs:
        errors = validate_retailer_config(config)
        if errors:
            validation_errors.extend([f"{config.name}: {error}" for error in errors])
    
    if validation_errors:
        console.print("❌ Configuration validation errors:", style="red")
        for error in validation_errors:
            console.print(f"  • {error}", style="red")
        raise typer.Exit(1)
    
    console.print("✅ Configuration validation passed")
    
    # Run basic tests
    console.print("🧪 Running basic tests...")
    try:
        # Test database connection
        db = get_database()
        deal_count = db.get_deal_count()
        console.print(f"✅ Database connection: {deal_count} deals stored")
        
        # Test ranker
        ranker = DealRanker()
        console.print("✅ Deal ranker initialized")
        
        # Test deduplicator
        deduplicator = DealDeduplicator()
        console.print("✅ Deal deduplicator initialized")
        
        # Test newsletter generator
        generator = NewsletterGenerator(NewsletterConfig())
        console.print("✅ Newsletter generator initialized")
        
        console.print("✅ All tests passed")
        
    except Exception as e:
        console.print(f"❌ Test failed: {str(e)}", style="red")
        raise typer.Exit(1)


@app.command()
def sources():
    """List configured sources."""
    console.print("📋 Configured sources:")
    
    configs = _load_retailer_configs()
    if not configs:
        console.print("❌ No sources configured", style="red")
        raise typer.Exit(1)
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Name", style="cyan")
    table.add_column("URL", style="green")
    table.add_column("Sport", style="yellow")
    table.add_column("Enabled", style="red")
    
    for config in configs:
        table.add_row(
            config.name,
            str(config.base_url),
            config.sport.value if config.sport else "Multi",
            "✅" if config.enabled else "❌"
        )
    
    console.print(table)


@app.command()
def stats():
    """Show database statistics."""
    console.print("📊 Database statistics:")
    
    db = get_database()
    
    # Get basic stats
    total_deals = db.get_deal_count()
    recent_deals = len(db.get_recent_deals(24))  # Last 24 hours
    
    # Get retailer stats
    retailer_stats = db.get_retailer_stats()
    
    # Show summary
    console.print(f"Total deals: {total_deals}")
    console.print(f"Recent deals (24h): {recent_deals}")
    
    if retailer_stats:
        console.print("\n📈 By retailer:")
        for retailer, stats in retailer_stats.items():
            console.print(f"  {retailer}: {stats['total_deals']} deals ({stats['youth_deals']} youth)")


@app.command()
def db():
    """Database management commands."""
    db = get_database()
    
    # Show database status
    total_deals = db.get_deal_count()
    console.print(f"📊 Database status: {total_deals} deals stored")
    
    # Show recent sessions
    sessions = db.get_scraping_sessions(limit=5)
    if sessions:
        console.print("\n🕒 Recent scraping sessions:")
        for session in sessions:
            status_emoji = "✅" if session.status == "completed" else "❌"
            console.print(f"  {status_emoji} {session.retailer}: {session.items_parsed} deals ({session.status})")


def _load_retailer_configs() -> List[RetailerConfig]:
    """Load retailer configurations from YAML file."""
    import yaml
    
    if not CONFIG_FILE.exists():
        console.print(f"❌ Configuration file not found: {CONFIG_FILE}", style="red")
        return []
    
    try:
        with open(CONFIG_FILE, 'r') as f:
            data = yaml.safe_load(f)
        
        configs = []
        for retailer_data in data.get('retailers', []):
            config = RetailerConfig(**retailer_data)
            configs.append(config)
        
        return configs
    except Exception as e:
        console.print(f"❌ Error loading configuration: {str(e)}", style="red")
        return []


async def _fetch_deals_from_sources(configs: List[RetailerConfig]) -> List[Deal]:
    """Fetch deals from all configured sources."""
    all_deals = []
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        
        for config in configs:
            if not config.enabled:
                continue
            
            task = progress.add_task(f"Fetching from {config.name}...", total=None)
            
            try:
                # Get appropriate collector
                collector = _get_collector(config)
                
                # Fetch deals
                async with collector:
                    deals = await collector.collect_deals()
                    all_deals.extend(deals)
                
                progress.update(task, description=f"✅ {config.name}: {len(deals)} deals")
                
            except Exception as e:
                progress.update(task, description=f"❌ {config.name}: {str(e)}")
                console.print(f"Error fetching from {config.name}: {str(e)}", style="red")
    
    return all_deals


def _get_collector(config: RetailerConfig):
    """Get appropriate collector for retailer configuration."""
    collector_map = {
        "dicks": DicksCollector,
        "academy": AcademyCollector,
        "scheels": ScheelsCollector,
        "big5": Big5Collector,
        "nike": NikeCollector,
        "adidas": AdidasCollector,
        "soccer.com": SoccerComCollector,
        "monkey sports": MonkeySportsCollector,
    }
    
    collector_class = collector_map.get(config.name.lower())
    if not collector_class:
        # Use base collector as fallback
        from .collectors.base import BaseCollector
        return BaseCollector(config)
    
    return collector_class(config)


def _filter_deals(deals: List[Deal], min_discount: float, youth_only: bool, max_deals: int) -> List[Deal]:
    """Filter deals based on criteria."""
    filtered = deals
    
    # Filter by minimum discount
    if min_discount > 0:
        filtered = [deal for deal in filtered if deal.discount_pct is None or deal.discount_pct >= min_discount]
    
    # Filter by youth only
    if youth_only:
        filtered = [deal for deal in filtered if deal.youth_flag]
    
    # Limit number of deals
    if max_deals > 0:
        filtered = filtered[:max_deals]
    
    return filtered


def _save_deals_to_file(deals: List[Deal], output_path: Path) -> None:
    """Save deals to file in JSON Lines format."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        for deal in deals:
            deal_dict = deal.model_dump(mode='json', exclude_none=True)
            f.write(json.dumps(deal_dict) + '\n')


def _show_fetch_summary(deals: List[Deal], configs: List[RetailerConfig]) -> None:
    """Show summary of fetched deals."""
    console.print(f"\n📊 Fetch Summary:")
    console.print(f"  Total deals: {len(deals)}")
    
    # Group by retailer
    retailer_counts = {}
    for deal in deals:
        retailer_counts[deal.retailer] = retailer_counts.get(deal.retailer, 0) + 1
    
    console.print(f"  By retailer:")
    for retailer, count in retailer_counts.items():
        console.print(f"    {retailer}: {count} deals")
    
    # Group by sport
    sport_counts = {}
    for deal in deals:
        if deal.sport:
            sport_counts[deal.sport.value] = sport_counts.get(deal.sport.value, 0) + 1
    
    if sport_counts:
        console.print(f"  By sport:")
        for sport, count in sport_counts.items():
            console.print(f"    {sport}: {count} deals")


def _show_ranking_summary(deals: List[Deal]) -> None:
    """Show summary of ranked deals."""
    console.print(f"\n📊 Ranking Summary:")
    console.print(f"  Top {len(deals)} deals by score")
    
    # Show top 5 deals
    console.print(f"  Top 5 deals:")
    for i, deal in enumerate(deals[:5], 1):
        score = deal.score or 0
        discount = deal.discount_pct or 0
        console.print(f"    {i}. {deal.title[:50]}... (Score: {score:.1f}, {discount:.0f}% off)")
    
    # Show score distribution
    scores = [deal.score or 0 for deal in deals]
    if scores:
        avg_score = sum(scores) / len(scores)
        max_score = max(scores)
        min_score = min(scores)
        console.print(f"  Score range: {min_score:.1f} - {max_score:.1f} (avg: {avg_score:.1f})")


if __name__ == "__main__":
    app()
