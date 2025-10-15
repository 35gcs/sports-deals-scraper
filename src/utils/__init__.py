"""Utility functions and helpers for the sports deals scraper."""

from .parsing import (
    clean_price,
    extract_brand_from_title,
    normalize_size,
    parse_price,
    parse_sizes,
    detect_youth_keywords,
    extract_json_ld,
    clean_text,
)

from .scoring import (
    calculate_discount_score,
    calculate_price_score,
    calculate_youth_score,
    calculate_brand_score,
    calculate_inventory_score,
    calculate_composite_score,
)

from .validation import (
    validate_url,
    validate_price,
    validate_retailer_config,
    is_valid_gtin,
    is_valid_mpn,
)

__all__ = [
    # Parsing utilities
    "clean_price",
    "extract_brand_from_title", 
    "normalize_size",
    "parse_price",
    "parse_sizes",
    "detect_youth_keywords",
    "extract_json_ld",
    "clean_text",
    
    # Scoring utilities
    "calculate_discount_score",
    "calculate_price_score", 
    "calculate_youth_score",
    "calculate_brand_score",
    "calculate_inventory_score",
    "calculate_composite_score",
    
    # Validation utilities
    "validate_url",
    "validate_price",
    "validate_retailer_config",
    "is_valid_gtin",
    "is_valid_mpn",
]
