"""Pytest configuration and fixtures."""

import pytest
from decimal import Decimal
from datetime import datetime
from pathlib import Path

from src.models import Deal, Sport, Category, Currency


@pytest.fixture
def sample_deal():
    """Create a sample deal for testing."""
    return Deal(
        id="test-deal-1",
        title="Nike Youth Soccer Cleats",
        brand="Nike",
        sport=Sport.SOCCER,
        category=Category.FOOTWEAR,
        youth_flag=True,
        sizes=["YS", "YM", "YL"],
        msrp=Decimal("80.00"),
        price=Decimal("40.00"),
        currency=Currency.USD,
        retailer="Dick's Sporting Goods",
        sku="NIKE-YOUTH-CLEATS-001",
        canonical_url="https://example.com/product/1",
        in_stock=True,
        last_seen=datetime.utcnow(),
    )


@pytest.fixture
def sample_deals():
    """Create multiple sample deals for testing."""
    return [
        Deal(
            id="deal-1",
            title="Adidas Youth Basketball Shoes",
            brand="Adidas",
            sport=Sport.BASKETBALL,
            category=Category.FOOTWEAR,
            youth_flag=True,
            sizes=["YS", "YM", "YL"],
            msrp=Decimal("90.00"),
            price=Decimal("45.00"),
            currency=Currency.USD,
            retailer="Academy Sports",
            sku="ADIDAS-YOUTH-BB-001",
            canonical_url="https://example.com/product/1",
            in_stock=True,
            last_seen=datetime.utcnow(),
        ),
        Deal(
            id="deal-2",
            title="Nike Adult Running Shoes",
            brand="Nike",
            sport=Sport.RUNNING,
            category=Category.FOOTWEAR,
            youth_flag=False,
            sizes=["M", "L", "XL"],
            msrp=Decimal("120.00"),
            price=Decimal("60.00"),
            currency=Currency.USD,
            retailer="Dick's Sporting Goods",
            sku="NIKE-ADULT-RUN-001",
            canonical_url="https://example.com/product/2",
            in_stock=True,
            last_seen=datetime.utcnow(),
        ),
        Deal(
            id="deal-3",
            title="Wilson Youth Baseball Glove",
            brand="Wilson",
            sport=Sport.BASEBALL,
            category=Category.EQUIPMENT,
            youth_flag=True,
            sizes=["11", "11.5", "12"],
            msrp=Decimal("60.00"),
            price=Decimal("30.00"),
            currency=Currency.USD,
            retailer="Big 5 Sporting Goods",
            sku="WILSON-YOUTH-GLOVE-001",
            canonical_url="https://example.com/product/3",
            in_stock=True,
            last_seen=datetime.utcnow(),
        ),
    ]


@pytest.fixture
def sample_html():
    """Sample HTML for testing parsers."""
    return """
    <div class="product-card">
        <img src="https://example.com/image.jpg" alt="Product Image">
        <div class="product-info">
            <h3 class="product-title">Nike Youth Soccer Cleats</h3>
            <div class="brand">Nike</div>
            <div class="price">
                <span class="sale-price">$40.00</span>
                <span class="was-price">$80.00</span>
            </div>
            <div class="sizes">
                <span class="size">YS</span>
                <span class="size">YM</span>
                <span class="size">YL</span>
            </div>
            <a href="/product/nike-youth-cleats" class="product-link">View Product</a>
        </div>
    </div>
    """


@pytest.fixture
def sample_json_ld():
    """Sample JSON-LD data for testing."""
    return {
        "@context": "https://schema.org",
        "@type": "Product",
        "name": "Nike Youth Soccer Cleats",
        "brand": {
            "@type": "Brand",
            "name": "Nike"
        },
        "sku": "NIKE-YOUTH-CLEATS-001",
        "gtin": "1234567890123",
        "image": "https://example.com/image.jpg",
        "offers": {
            "@type": "Offer",
            "price": "40.00",
            "priceCurrency": "USD",
            "availability": "https://schema.org/InStock"
        }
    }


@pytest.fixture
def test_data_dir():
    """Path to test data directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_retailer_config():
    """Sample retailer configuration for testing."""
    from src.models import RetailerConfig
    
    return RetailerConfig(
        name="Test Retailer",
        base_url="https://example.com/sale",
        enabled=True,
        selectors={
            "item": ".product-card",
            "title": ".product-title",
            "price": ".price .sale-price",
            "msrp": ".price .was-price",
            "url": "a::attr(href)",
            "image": "img::attr(src)",
        },
        sport=Sport.SOCCER,
        youth_keywords=["youth", "jr", "kids"],
        rate_limit={"requests_per_minute": 10, "burst": 3},
    )
