"""Integration tests for the sports deals scraper."""

import pytest
from pathlib import Path

from src.models import Deal, NewsletterConfig
from src.ranker import DealRanker
from src.deduplicator import DealDeduplicator
from src.newsletter import NewsletterGenerator


def test_ranker_integration(sample_deals):
    """Test ranker integration with sample deals."""
    ranker = DealRanker(min_discount=20.0)
    
    # Test ranking
    ranked_deals = ranker.rank_deals(sample_deals)
    assert len(ranked_deals) <= len(sample_deals)
    
    # Test grouping by sport
    sport_deals = ranker.get_top_deals_by_sport(sample_deals, top_per_sport=2)
    assert len(sport_deals) > 0
    
    # Test youth filtering
    youth_deals = ranker.get_youth_deals(sample_deals)
    assert all(deal.youth_flag for deal in youth_deals)
    
    # Test summary generation
    summary = ranker.get_deals_summary(sample_deals)
    assert "total_deals" in summary
    assert "youth_deals" in summary
    assert "avg_discount" in summary


def test_deduplicator_integration(sample_deals):
    """Test deduplicator integration with sample deals."""
    deduplicator = DealDeduplicator(similarity_threshold=0.8)
    
    # Test deduplication
    canonical_deals = deduplicator.deduplicate_deals(sample_deals)
    assert len(canonical_deals) <= len(sample_deals)
    
    # Test duplicate detection
    duplicates = deduplicator.find_duplicates(sample_deals)
    assert isinstance(duplicates, list)
    
    # Test statistics
    stats = deduplicator.get_deduplication_stats(sample_deals)
    assert "total_deals" in stats
    assert "canonical_deals" in stats
    assert "duplicate_groups" in stats


def test_newsletter_generation_integration(sample_deals):
    """Test newsletter generation integration."""
    config = NewsletterConfig(
        title="Test Newsletter",
        top_per_sport=2,
        min_discount_pct=20.0,
        show_youth_only=True,
        formats=["html", "markdown"],
        output_dir="test_out"
    )
    
    generator = NewsletterGenerator(config)
    
    # Test newsletter generation
    week = "2025-W01"
    newsletters = generator.generate_newsletter(sample_deals, week)
    
    assert "html" in newsletters
    assert "markdown" in newsletters
    
    # Check that HTML contains expected content
    html_content = newsletters["html"]
    assert "Test Newsletter" in html_content
    assert "Week 2025-W01" in html_content
    
    # Check that Markdown contains expected content
    markdown_content = newsletters["markdown"]
    assert "# Test Newsletter" in markdown_content
    assert "Week 2025-W01" in markdown_content


def test_end_to_end_workflow(sample_deals):
    """Test complete end-to-end workflow."""
    # Step 1: Rank deals
    ranker = DealRanker(min_discount=20.0)
    ranked_deals = ranker.rank_deals(sample_deals)
    
    # Step 2: Deduplicate deals
    deduplicator = DealDeduplicator()
    canonical_deals = deduplicator.deduplicate_deals(ranked_deals)
    
    # Step 3: Generate newsletter
    config = NewsletterConfig(
        title="End-to-End Test Newsletter",
        top_per_sport=2,
        min_discount_pct=20.0,
        show_youth_only=True,
        formats=["html", "markdown"],
        output_dir="test_out"
    )
    
    generator = NewsletterGenerator(config)
    newsletters = generator.generate_newsletter(canonical_deals, "2025-W01")
    
    # Verify results
    assert len(canonical_deals) <= len(ranked_deals)
    assert len(newsletters) == 2
    assert "html" in newsletters
    assert "markdown" in newsletters
    
    # Check that all deals have scores
    for deal in canonical_deals:
        assert deal.score is not None
        assert deal.score >= 0
        assert deal.score <= 100


def test_newsletter_stats(sample_deals):
    """Test newsletter statistics generation."""
    config = NewsletterConfig(
        title="Stats Test Newsletter",
        top_per_sport=2,
        min_discount_pct=20.0,
        show_youth_only=True,
        formats=["html", "markdown"],
        output_dir="test_out"
    )
    
    generator = NewsletterGenerator(config)
    stats = generator.get_newsletter_stats(sample_deals)
    
    assert "total_deals" in stats
    assert "sport_counts" in stats
    assert "category_counts" in stats
    assert "sports_covered" in stats
    assert "categories_covered" in stats
    
    # Verify stats are reasonable
    assert stats["total_deals"] >= 0
    assert stats["sports_covered"] >= 0
    assert stats["categories_covered"] >= 0


def test_deal_serialization(sample_deals):
    """Test deal serialization for storage."""
    for deal in sample_deals:
        # Test serialization to dict
        deal_dict = deal.to_dict()
        assert isinstance(deal_dict, dict)
        assert "id" in deal_dict
        assert "title" in deal_dict
        assert "price" in deal_dict
        assert "retailer" in deal_dict
        
        # Test that all required fields are present
        required_fields = ["id", "title", "price", "retailer", "canonical_url"]
        for field in required_fields:
            assert field in deal_dict


def test_deal_validation(sample_deals):
    """Test deal validation."""
    for deal in sample_deals:
        # Test that all deals are valid
        assert deal.id is not None
        assert deal.title is not None
        assert deal.price is not None
        assert deal.retailer is not None
        assert deal.canonical_url is not None
        
        # Test price validation
        assert float(deal.price) >= 0
        
        # Test URL validation
        assert str(deal.canonical_url).startswith("http")
        
        # Test discount calculation
        if deal.msrp and deal.msrp > 0:
            assert deal.discount_pct is not None
            assert deal.discount_pct >= 0
            assert deal.discount_pct <= 100


def test_newsletter_file_generation(sample_deals, tmp_path):
    """Test newsletter file generation."""
    config = NewsletterConfig(
        title="File Test Newsletter",
        top_per_sport=2,
        min_discount_pct=20.0,
        show_youth_only=True,
        formats=["html", "markdown"],
        output_dir=str(tmp_path)
    )
    
    generator = NewsletterGenerator(config)
    newsletters = generator.generate_newsletter(sample_deals, "2025-W01")
    
    # Save newsletters
    saved_files = generator.save_newsletter(newsletters, "2025-W01")
    
    # Verify files were created
    assert "html" in saved_files
    assert "markdown" in saved_files
    
    html_file = saved_files["html"]
    markdown_file = saved_files["markdown"]
    
    assert html_file.exists()
    assert markdown_file.exists()
    
    # Verify file contents
    html_content = html_file.read_text()
    markdown_content = markdown_file.read_text()
    
    assert "File Test Newsletter" in html_content
    assert "File Test Newsletter" in markdown_content
    assert "Week 2025-W01" in html_content
    assert "Week 2025-W01" in markdown_content
