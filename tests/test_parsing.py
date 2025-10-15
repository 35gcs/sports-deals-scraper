"""Tests for parsing utilities."""

import pytest
from decimal import Decimal

from src.utils.parsing import (
    clean_text,
    parse_price,
    extract_brand_from_title,
    parse_sizes,
    detect_youth_keywords,
    extract_json_ld,
    extract_product_data_from_json_ld,
    normalize_url,
    extract_coupon_code,
)


def test_clean_text():
    """Test text cleaning functionality."""
    # Test basic cleaning
    assert clean_text("  Hello   World  ") == "Hello World"
    
    # Test HTML entity replacement
    assert clean_text("Hello &amp; World") == "Hello & World"
    assert clean_text("Price &lt; $50") == "Price < $50"
    
    # Test empty/None input
    assert clean_text("") == ""
    assert clean_text(None) == ""


def test_parse_price():
    """Test price parsing functionality."""
    # Test various price formats
    assert parse_price("$25.99") == Decimal("25.99")
    assert parse_price("25.99") == Decimal("25.99")
    assert parse_price("$1,234.56") == Decimal("1234.56")
    assert parse_price("Price: $45.00") == Decimal("45.00")
    assert parse_price("Was $80.00") == Decimal("80.00")
    
    # Test invalid prices
    assert parse_price("") is None
    assert parse_price("Free") is None
    assert parse_price("Invalid price") is None


def test_extract_brand_from_title():
    """Test brand extraction from titles."""
    # Test brand extraction
    assert extract_brand_from_title("Nike Youth Soccer Cleats") == "Nike"
    assert extract_brand_from_title("Adidas Running Shoes") == "Adidas"
    assert extract_brand_from_title("NIKE BASKETBALL SHOES") == "NIKE"
    
    # Test titles without clear brands
    assert extract_brand_from_title("Youth Soccer Cleats") is None
    assert extract_brand_from_title("The Best Running Shoes") is None


def test_parse_sizes():
    """Test size parsing functionality."""
    # Test various size formats
    sizes = parse_sizes("Sizes: S, M, L, XL")
    assert "S" in sizes
    assert "M" in sizes
    assert "L" in sizes
    assert "XL" in sizes
    
    # Test youth sizes
    youth_sizes = parse_sizes("Available in YS, YM, YL, YXL")
    assert "YS" in youth_sizes
    assert "YM" in youth_sizes
    assert "YL" in youth_sizes
    assert "YXL" in youth_sizes
    
    # Test numeric sizes
    numeric_sizes = parse_sizes("Sizes 8, 9, 10, 11")
    assert "8" in numeric_sizes
    assert "9" in numeric_sizes
    assert "10" in numeric_sizes
    assert "11" in numeric_sizes


def test_detect_youth_keywords():
    """Test youth keyword detection."""
    # Test positive cases
    assert detect_youth_keywords("Nike Youth Soccer Cleats") is True
    assert detect_youth_keywords("Jr Basketball Shoes") is True
    assert detect_youth_keywords("Kids Running Shoes") is True
    assert detect_youth_keywords("Boy's Soccer Jersey") is True
    assert detect_youth_keywords("Girl's Tennis Dress") is True
    
    # Test negative cases
    assert detect_youth_keywords("Nike Adult Running Shoes") is False
    assert detect_youth_keywords("Men's Basketball Shoes") is False
    assert detect_youth_keywords("Women's Tennis Dress") is False
    
    # Test mixed case
    assert detect_youth_keywords("NIKE YOUTH SOCCER CLEATS") is True
    assert detect_youth_keywords("nike youth soccer cleats") is True


def test_extract_json_ld():
    """Test JSON-LD extraction from HTML."""
    html = """
    <html>
        <head>
            <script type="application/ld+json">
            {
                "@type": "Product",
                "name": "Test Product"
            }
            </script>
        </head>
        <body>
            <script type="application/ld+json">
            {
                "@type": "Offer",
                "price": "25.99"
            }
            </script>
        </body>
    </html>
    """
    
    json_ld_data = extract_json_ld(html)
    assert len(json_ld_data) == 2
    assert json_ld_data[0]["@type"] == "Product"
    assert json_ld_data[1]["@type"] == "Offer"


def test_extract_product_data_from_json_ld():
    """Test product data extraction from JSON-LD."""
    json_ld_data = [
        {
            "@type": "Product",
            "name": "Nike Youth Soccer Cleats",
            "brand": {
                "@type": "Brand",
                "name": "Nike"
            },
            "sku": "NIKE-YOUTH-001",
            "gtin": "1234567890123",
            "image": "https://example.com/image.jpg",
            "offers": {
                "@type": "Offer",
                "price": "40.00",
                "priceCurrency": "USD",
                "availability": "https://schema.org/InStock"
            }
        }
    ]
    
    product_data = extract_product_data_from_json_ld(json_ld_data)
    
    assert product_data["title"] == "Nike Youth Soccer Cleats"
    assert product_data["brand"] == "Nike"
    assert product_data["sku"] == "NIKE-YOUTH-001"
    assert product_data["gtin"] == "1234567890123"
    assert product_data["image_url"] == "https://example.com/image.jpg"
    assert product_data["price"] == Decimal("40.00")
    assert product_data["currency"] == "USD"
    assert product_data["in_stock"] is True


def test_normalize_url():
    """Test URL normalization."""
    base_url = "https://example.com"
    
    # Test relative URLs
    assert normalize_url("/product/1", base_url) == "https://example.com/product/1"
    assert normalize_url("product/1", base_url) == "https://example.com/product/1"
    
    # Test absolute URLs
    assert normalize_url("https://other.com/product/1", base_url) == "https://other.com/product/1"
    
    # Test protocol-relative URLs
    assert normalize_url("//other.com/product/1", base_url) == "https://other.com/product/1"


def test_extract_coupon_code():
    """Test coupon code extraction."""
    # Test various coupon formats
    assert extract_coupon_code("Use code SAVE20 for 20% off") == "SAVE20"
    assert extract_coupon_code("Coupon: DISCOUNT15") == "DISCOUNT15"
    assert extract_coupon_code("Save with code WELCOME10") == "WELCOME10"
    assert extract_coupon_code("Code: SUMMER25 discount") == "SUMMER25"
    
    # Test no coupon cases
    assert extract_coupon_code("No coupon available") is None
    assert extract_coupon_code("") is None
