"""Validation utilities for data integrity and configuration validation."""

import re
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from ..models import RetailerConfig


def validate_url(url: str) -> bool:
    """Validate URL format and accessibility."""
    if not url:
        return False
    
    try:
        parsed = urlparse(url)
        return bool(parsed.scheme and parsed.netloc)
    except Exception:
        return False


def validate_price(price: Any) -> bool:
    """Validate price value."""
    if price is None:
        return False
    
    try:
        if isinstance(price, (int, float)):
            return price >= 0
        elif isinstance(price, str):
            # Try to parse as float
            float_price = float(price)
            return float_price >= 0
        return False
    except (ValueError, TypeError):
        return False


def is_valid_gtin(gtin: str) -> bool:
    """Validate GTIN (Global Trade Item Number) format."""
    if not gtin:
        return False
    
    # Remove any non-digit characters
    digits = re.sub(r'\D', '', gtin)
    
    # GTIN can be 8, 12, 13, or 14 digits
    if len(digits) not in [8, 12, 13, 14]:
        return False
    
    # Validate check digit using Luhn algorithm
    return _validate_gtin_check_digit(digits)


def _validate_gtin_check_digit(gtin: str) -> bool:
    """Validate GTIN check digit using Luhn algorithm."""
    if len(gtin) < 2:
        return False
    
    # Get check digit (last digit)
    check_digit = int(gtin[-1])
    
    # Calculate expected check digit
    digits = [int(d) for d in gtin[:-1]]
    
    # Apply Luhn algorithm
    total = 0
    for i, digit in enumerate(reversed(digits)):
        if i % 2 == 0:  # Even positions (0-indexed)
            doubled = digit * 2
            total += doubled if doubled < 10 else doubled - 9
        else:  # Odd positions
            total += digit
    
    expected_check = (10 - (total % 10)) % 10
    return check_digit == expected_check


def is_valid_mpn(mpn: str) -> bool:
    """Validate MPN (Manufacturer Part Number) format."""
    if not mpn:
        return False
    
    # MPN should be alphanumeric with some special characters
    # Common patterns: letters, numbers, hyphens, underscores, dots
    mpn_pattern = r'^[A-Za-z0-9\-_\.]+$'
    
    if not re.match(mpn_pattern, mpn):
        return False
    
    # Should be reasonable length (2-50 characters)
    if len(mpn) < 2 or len(mpn) > 50:
        return False
    
    return True


def validate_retailer_config(config: RetailerConfig) -> List[str]:
    """Validate retailer configuration and return list of errors."""
    errors = []
    
    # Validate name
    if not config.name or len(config.name.strip()) < 2:
        errors.append("Retailer name must be at least 2 characters")
    
    # Validate base URL
    if not validate_url(str(config.base_url)):
        errors.append("Invalid base URL format")
    
    # Validate selectors
    required_selectors = ['item', 'title', 'price']
    for selector in required_selectors:
        if selector not in config.selectors:
            errors.append(f"Missing required selector: {selector}")
        elif not config.selectors[selector].strip():
            errors.append(f"Empty selector: {selector}")
    
    # Validate rate limits
    if config.rate_limit.get('requests_per_minute', 0) <= 0:
        errors.append("requests_per_minute must be positive")
    
    if config.rate_limit.get('burst', 0) <= 0:
        errors.append("burst must be positive")
    
    # Validate pagination if provided
    if config.pagination:
        pagination_errors = _validate_pagination_config(config.pagination)
        errors.extend(pagination_errors)
    
    # Validate youth keywords if provided
    if config.youth_keywords:
        for keyword in config.youth_keywords:
            if not keyword or not keyword.strip():
                errors.append("Empty youth keyword found")
    
    return errors


def _validate_pagination_config(pagination: Dict[str, Any]) -> List[str]:
    """Validate pagination configuration."""
    errors = []
    
    pagination_type = pagination.get('type')
    if not pagination_type:
        errors.append("Pagination type is required")
        return errors
    
    if pagination_type == 'page_param':
        if 'param' not in pagination:
            errors.append("Page parameter name is required for page_param type")
        if 'start' not in pagination:
            errors.append("Start page number is required for page_param type")
        elif not isinstance(pagination['start'], int) or pagination['start'] < 1:
            errors.append("Start page must be a positive integer")
    
    elif pagination_type == 'offset':
        if 'limit' not in pagination:
            errors.append("Limit is required for offset type")
        elif not isinstance(pagination['limit'], int) or pagination['limit'] < 1:
            errors.append("Limit must be a positive integer")
    
    elif pagination_type == 'scroll':
        # Scroll pagination doesn't need additional validation
        pass
    
    else:
        errors.append(f"Unknown pagination type: {pagination_type}")
    
    return errors


def validate_deal_data(deal_data: Dict[str, Any]) -> List[str]:
    """Validate deal data before creating Deal object."""
    errors = []
    
    # Required fields
    required_fields = ['title', 'price', 'retailer', 'canonical_url']
    for field in required_fields:
        if field not in deal_data or not deal_data[field]:
            errors.append(f"Missing required field: {field}")
    
    # Validate price
    if 'price' in deal_data and not validate_price(deal_data['price']):
        errors.append("Invalid price value")
    
    # Validate MSRP if provided
    if 'msrp' in deal_data and deal_data['msrp'] is not None:
        if not validate_price(deal_data['msrp']):
            errors.append("Invalid MSRP value")
        elif deal_data['msrp'] < deal_data.get('price', 0):
            errors.append("MSRP cannot be less than current price")
    
    # Validate URLs
    if 'canonical_url' in deal_data and not validate_url(deal_data['canonical_url']):
        errors.append("Invalid canonical URL")
    
    if 'image_url' in deal_data and deal_data['image_url']:
        if not validate_url(deal_data['image_url']):
            errors.append("Invalid image URL")
    
    # Validate GTIN if provided
    if 'gtin' in deal_data and deal_data['gtin']:
        if not is_valid_gtin(deal_data['gtin']):
            errors.append("Invalid GTIN format")
    
    # Validate MPN if provided
    if 'mpn' in deal_data and deal_data['mpn']:
        if not is_valid_mpn(deal_data['mpn']):
            errors.append("Invalid MPN format")
    
    # Validate sizes if provided
    if 'sizes' in deal_data and deal_data['sizes']:
        if not isinstance(deal_data['sizes'], list):
            errors.append("Sizes must be a list")
        elif not all(isinstance(size, str) and size.strip() for size in deal_data['sizes']):
            errors.append("All sizes must be non-empty strings")
    
    return errors


def validate_newsletter_config(config_data: Dict[str, Any]) -> List[str]:
    """Validate newsletter configuration."""
    errors = []
    
    # Validate title
    if 'title' in config_data:
        title = config_data['title']
        if not isinstance(title, str) or len(title.strip()) < 3:
            errors.append("Newsletter title must be at least 3 characters")
    
    # Validate numeric fields
    numeric_fields = ['top_per_sport', 'min_discount_pct', 'max_deals_total']
    for field in numeric_fields:
        if field in config_data:
            value = config_data[field]
            if not isinstance(value, (int, float)) or value < 0:
                errors.append(f"{field} must be a non-negative number")
    
    # Validate formats
    if 'formats' in config_data:
        formats = config_data['formats']
        if not isinstance(formats, list):
            errors.append("Formats must be a list")
        else:
            valid_formats = ['html', 'markdown']
            for fmt in formats:
                if fmt not in valid_formats:
                    errors.append(f"Invalid format: {fmt}. Must be one of {valid_formats}")
    
    # Validate theme
    if 'theme' in config_data:
        theme = config_data['theme']
        if theme not in ['light', 'dark', 'auto']:
            errors.append("Theme must be one of: light, dark, auto")
    
    return errors


def sanitize_text(text: str, max_length: Optional[int] = None) -> str:
    """Sanitize text by removing dangerous characters and limiting length."""
    if not text:
        return ""
    
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    
    # Remove control characters except newlines and tabs
    text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
    
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text.strip())
    
    # Limit length if specified
    if max_length and len(text) > max_length:
        text = text[:max_length-3] + "..."
    
    return text


def validate_css_selector(selector: str) -> bool:
    """Validate CSS selector syntax."""
    if not selector or not selector.strip():
        return False
    
    # Basic validation - check for common CSS selector patterns
    # This is not comprehensive but catches obvious errors
    valid_patterns = [
        r'^[.#]?[a-zA-Z][a-zA-Z0-9_-]*$',  # Simple class/id/element
        r'^[.#]?[a-zA-Z][a-zA-Z0-9_-]*\s+[.#]?[a-zA-Z][a-zA-Z0-9_-]*$',  # Descendant
        r'^[.#]?[a-zA-Z][a-zA-Z0-9_-]*\[[^]]+\]$',  # Attribute selector
        r'^[.#]?[a-zA-Z][a-zA-Z0-9_-]*:[a-zA-Z-]+$',  # Pseudo-selector
    ]
    
    return any(re.match(pattern, selector.strip()) for pattern in valid_patterns)


def validate_xpath_selector(xpath: str) -> bool:
    """Validate XPath selector syntax."""
    if not xpath or not xpath.strip():
        return False
    
    # Basic XPath validation
    # Check for common XPath patterns and syntax
    try:
        # This is a basic check - in production you might want to use lxml for validation
        if not xpath.startswith(('/', '//', '.', '..', '@')):
            # Must start with valid XPath axis
            return False
        
        # Check for balanced brackets
        if xpath.count('[') != xpath.count(']'):
            return False
        
        # Check for balanced quotes
        single_quotes = xpath.count("'")
        double_quotes = xpath.count('"')
        if single_quotes % 2 != 0 or double_quotes % 2 != 0:
            return False
        
        return True
    except Exception:
        return False
