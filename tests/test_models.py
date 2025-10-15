"""Tests for Pydantic models."""

import pytest
from decimal import Decimal
from datetime import datetime

from src.models import Deal, Sport, Category, Currency, SizeType


def test_deal_creation(sample_deal):
    """Test basic deal creation."""
    assert sample_deal.title == "Nike Youth Soccer Cleats"
    assert sample_deal.brand == "Nike"
    assert sample_deal.sport == Sport.SOCCER
    assert sample_deal.category == Category.FOOTWEAR
    assert sample_deal.youth_flag is True
    assert sample_deal.price == Decimal("40.00")
    assert sample_deal.msrp == Decimal("80.00")


def test_deal_discount_calculation(sample_deal):
    """Test discount percentage calculation."""
    assert sample_deal.discount_pct == 50.0


def test_deal_savings_calculation(sample_deal):
    """Test savings amount calculation."""
    assert sample_deal.savings_amount == Decimal("40.00")


def test_deal_youth_detection():
    """Test youth detection logic."""
    # Youth deal
    youth_deal = Deal(
        id="youth-1",
        title="Nike Youth Soccer Cleats",
        price=Decimal("40.00"),
        retailer="Test",
        canonical_url="https://example.com/1",
        sizes=["YS", "YM", "YL"]
    )
    assert youth_deal.is_youth_sized() is True
    
    # Adult deal
    adult_deal = Deal(
        id="adult-1",
        title="Nike Adult Running Shoes",
        price=Decimal("80.00"),
        retailer="Test",
        canonical_url="https://example.com/2",
        sizes=["M", "L", "XL"]
    )
    assert adult_deal.is_youth_sized() is False


def test_deal_id_generation():
    """Test automatic ID generation."""
    deal = Deal(
        title="Test Product",
        price=Decimal("50.00"),
        retailer="Test",
        canonical_url="https://example.com/test"
    )
    assert deal.id is not None
    assert len(deal.id) == 16


def test_deal_validation():
    """Test deal validation."""
    # Valid deal
    valid_deal = Deal(
        title="Valid Product",
        price=Decimal("50.00"),
        retailer="Test",
        canonical_url="https://example.com/valid"
    )
    assert valid_deal.title == "Valid Product"
    
    # Invalid URL should raise error
    with pytest.raises(ValueError):
        Deal(
            title="Invalid Product",
            price=Decimal("50.00"),
            retailer="Test",
            canonical_url="invalid-url"
        )


def test_deal_serialization(sample_deal):
    """Test deal serialization to dict."""
    deal_dict = sample_deal.to_dict()
    assert isinstance(deal_dict, dict)
    assert deal_dict["title"] == "Nike Youth Soccer Cleats"
    assert deal_dict["price"] == "40.00"
    assert deal_dict["brand"] == "Nike"


def test_deal_effective_price(sample_deal):
    """Test effective price calculation."""
    assert sample_deal.get_effective_price() == Decimal("40.00")


def test_deal_size_normalization():
    """Test size normalization."""
    deal = Deal(
        id="size-test",
        title="Test Product",
        price=Decimal("50.00"),
        retailer="Test",
        canonical_url="https://example.com/test",
        sizes=["ys", "YM", "xl", ""]
    )
    # Empty sizes should be filtered out
    assert deal.sizes == ["YS", "YM", "XL"]


def test_deal_currency_default():
    """Test default currency assignment."""
    deal = Deal(
        title="Test Product",
        price=Decimal("50.00"),
        retailer="Test",
        canonical_url="https://example.com/test"
    )
    assert deal.currency == Currency.USD


def test_deal_timestamps():
    """Test timestamp handling."""
    deal = Deal(
        title="Test Product",
        price=Decimal("50.00"),
        retailer="Test",
        canonical_url="https://example.com/test"
    )
    assert deal.last_seen is not None
    assert deal.first_seen == deal.last_seen
