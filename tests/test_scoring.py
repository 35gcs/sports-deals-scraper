"""Tests for scoring and ranking utilities."""

import pytest
from decimal import Decimal

from src.models import Deal, Sport, Category, Currency
from src.utils.scoring import (
    calculate_discount_score,
    calculate_price_score,
    calculate_youth_score,
    calculate_brand_score,
    calculate_inventory_score,
    calculate_composite_score,
    rank_deals,
    get_top_deals_by_sport,
)


def test_calculate_discount_score():
    """Test discount score calculation."""
    # Test high discount
    deal = Deal(
        id="test-1",
        title="Test Product",
        price=Decimal("20.00"),
        msrp=Decimal("100.00"),
        retailer="Test",
        canonical_url="https://example.com/1"
    )
    score = calculate_discount_score(deal)
    assert score == 45.0  # 80% discount, capped at 45
    
    # Test medium discount
    deal = Deal(
        id="test-2",
        title="Test Product",
        price=Decimal("60.00"),
        msrp=Decimal("100.00"),
        retailer="Test",
        canonical_url="https://example.com/2"
    )
    score = calculate_discount_score(deal)
    assert score == 36.0  # 40% discount
    
    # Test no discount
    deal = Deal(
        id="test-3",
        title="Test Product",
        price=Decimal("100.00"),
        retailer="Test",
        canonical_url="https://example.com/3"
    )
    score = calculate_discount_score(deal)
    assert score == 0.0


def test_calculate_price_score():
    """Test price score calculation."""
    # Test low price (high score)
    deal = Deal(
        id="test-1",
        title="Test Product",
        price=Decimal("15.00"),
        retailer="Test",
        canonical_url="https://example.com/1"
    )
    score = calculate_price_score(deal)
    assert score == 20.0
    
    # Test medium price
    deal = Deal(
        id="test-2",
        title="Test Product",
        price=Decimal("50.00"),
        retailer="Test",
        canonical_url="https://example.com/2"
    )
    score = calculate_price_score(deal)
    assert score == 12.5
    
    # Test high price (low score)
    deal = Deal(
        id="test-3",
        title="Test Product",
        price=Decimal("150.00"),
        retailer="Test",
        canonical_url="https://example.com/3"
    )
    score = calculate_price_score(deal)
    assert score == 2.5


def test_calculate_youth_score():
    """Test youth score calculation."""
    # Test youth deal
    deal = Deal(
        id="test-1",
        title="Nike Youth Soccer Cleats",
        price=Decimal("40.00"),
        retailer="Test",
        canonical_url="https://example.com/1",
        youth_flag=True,
        sizes=["YS", "YM", "YL"]
    )
    score = calculate_youth_score(deal)
    assert score == 20.0  # Full youth score
    
    # Test adult deal
    deal = Deal(
        id="test-2",
        title="Nike Adult Running Shoes",
        price=Decimal("80.00"),
        retailer="Test",
        canonical_url="https://example.com/2",
        youth_flag=False,
        sizes=["M", "L", "XL"]
    )
    score = calculate_youth_score(deal)
    assert score == 0.0
    
    # Test ambiguous deal with youth sizes
    deal = Deal(
        id="test-3",
        title="Soccer Cleats",
        price=Decimal("50.00"),
        retailer="Test",
        canonical_url="https://example.com/3",
        youth_flag=False,
        sizes=["YS", "YM", "YL"]
    )
    score = calculate_youth_score(deal)
    assert score > 0  # Should get some youth score from sizes


def test_calculate_brand_score():
    """Test brand score calculation."""
    # Test premium brand
    deal = Deal(
        id="test-1",
        title="Nike Soccer Cleats",
        price=Decimal("80.00"),
        retailer="Test",
        canonical_url="https://example.com/1",
        brand="Nike"
    )
    score = calculate_brand_score(deal)
    assert score == 8.5  # Nike brand score
    
    # Test unknown brand
    deal = Deal(
        id="test-2",
        title="Generic Soccer Cleats",
        price=Decimal("40.00"),
        retailer="Test",
        canonical_url="https://example.com/2",
        brand="Generic Brand"
    )
    score = calculate_brand_score(deal)
    assert score == 5.0  # Default brand score
    
    # Test sport-specific brand
    deal = Deal(
        id="test-3",
        title="Bauer Hockey Stick",
        price=Decimal("100.00"),
        retailer="Test",
        canonical_url="https://example.com/3",
        brand="Bauer",
        sport=Sport.HOCKEY
    )
    score = calculate_brand_score(deal)
    assert score == 10.0  # Bauer base score + hockey bonus


def test_calculate_inventory_score():
    """Test inventory score calculation."""
    # Test in stock deal
    deal = Deal(
        id="test-1",
        title="Test Product",
        price=Decimal("50.00"),
        retailer="Test",
        canonical_url="https://example.com/1",
        in_stock=True,
        sizes=["S", "M", "L"],
        coupon_code="SAVE10"
    )
    score = calculate_inventory_score(deal)
    assert score == 5.0  # In stock + good sizes + coupon
    
    # Test out of stock deal
    deal = Deal(
        id="test-2",
        title="Test Product",
        price=Decimal("50.00"),
        retailer="Test",
        canonical_url="https://example.com/2",
        in_stock=False
    )
    score = calculate_inventory_score(deal)
    assert score == 0.0  # Out of stock penalty
    
    # Test limited stock deal
    deal = Deal(
        id="test-3",
        title="Test Product",
        price=Decimal("50.00"),
        retailer="Test",
        canonical_url="https://example.com/3",
        in_stock=True,
        stock_level="limited"
    )
    score = calculate_inventory_score(deal)
    assert score == 3.0  # In stock + limited stock bonus


def test_calculate_composite_score():
    """Test composite score calculation."""
    # Test high-scoring deal
    deal = Deal(
        id="test-1",
        title="Nike Youth Soccer Cleats",
        price=Decimal("20.00"),
        msrp=Decimal("80.00"),
        retailer="Test",
        canonical_url="https://example.com/1",
        brand="Nike",
        youth_flag=True,
        in_stock=True,
        sizes=["YS", "YM", "YL"],
        coupon_code="SAVE20"
    )
    score = calculate_composite_score(deal)
    assert score > 80  # Should be a high score
    
    # Test low-scoring deal
    deal = Deal(
        id="test-2",
        title="Generic Adult Shoes",
        price=Decimal("100.00"),
        retailer="Test",
        canonical_url="https://example.com/2",
        brand="Generic",
        youth_flag=False,
        in_stock=False
    )
    score = calculate_composite_score(deal)
    assert score < 30  # Should be a low score


def test_rank_deals(sample_deals):
    """Test deal ranking functionality."""
    # Add scores to deals
    for deal in sample_deals:
        deal.score = calculate_composite_score(deal)
    
    # Rank deals
    ranked = rank_deals(sample_deals, min_discount=0.0)
    
    # Check that deals are sorted by score (descending)
    for i in range(len(ranked) - 1):
        assert ranked[i].score >= ranked[i + 1].score
    
    # Check that all deals are included
    assert len(ranked) == len(sample_deals)


def test_get_top_deals_by_sport(sample_deals):
    """Test getting top deals by sport."""
    # Add scores to deals
    for deal in sample_deals:
        deal.score = calculate_composite_score(deal)
    
    # Get top deals by sport
    sport_deals = get_top_deals_by_sport(sample_deals, top_per_sport=2)
    
    # Check that we have deals for each sport
    assert Sport.BASKETBALL in sport_deals
    assert Sport.RUNNING in sport_deals
    assert Sport.BASEBALL in sport_deals
    
    # Check that each sport has at most 2 deals
    for sport, deals in sport_deals.items():
        assert len(deals) <= 2
        
        # Check that deals are sorted by score
        for i in range(len(deals) - 1):
            assert deals[i].score >= deals[i + 1].score


def test_score_edge_cases():
    """Test scoring with edge cases."""
    # Test deal with no MSRP
    deal = Deal(
        id="test-1",
        title="Test Product",
        price=Decimal("50.00"),
        retailer="Test",
        canonical_url="https://example.com/1"
    )
    score = calculate_composite_score(deal)
    assert score >= 0  # Should not crash
    
    # Test deal with zero price
    deal = Deal(
        id="test-2",
        title="Free Product",
        price=Decimal("0.00"),
        retailer="Test",
        canonical_url="https://example.com/2"
    )
    score = calculate_composite_score(deal)
    assert score >= 0  # Should not crash
    
    # Test deal with very high discount (potential fake MSRP)
    deal = Deal(
        id="test-3",
        title="Test Product",
        price=Decimal("10.00"),
        msrp=Decimal("1000.00"),  # 99% discount
        retailer="Test",
        canonical_url="https://example.com/3"
    )
    score = calculate_composite_score(deal)
    assert score <= 100  # Should be capped
