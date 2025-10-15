"""Parsing utilities for extracting data from HTML and text."""

import re
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urljoin, urlparse

import json
from html.parser import HTMLParser as _HTMLParser


class _JSONLDScriptExtractor(_HTMLParser):
    """Simple HTML parser to extract JSON-LD script contents."""

    def __init__(self) -> None:
        super().__init__()
        self._capture = False
        self._buffer: List[str] = []
        self.scripts: List[str] = []

    def handle_starttag(self, tag: str, attrs):  # type: ignore[override]
        if tag.lower() != "script":
            return

        attributes = {name.lower(): value for name, value in attrs}
        if attributes.get("type", "").lower() == "application/ld+json":
            self._capture = True
            self._buffer = []

    def handle_endtag(self, tag: str):  # type: ignore[override]
        if tag.lower() == "script" and self._capture:
            self._capture = False
            script_content = "".join(self._buffer).strip()
            if script_content:
                self.scripts.append(script_content)
            self._buffer = []

    def handle_data(self, data: str):  # type: ignore[override]
        if self._capture:
            self._buffer.append(data)


def clean_text(text: str) -> str:
    """Clean and normalize text content."""
    if not text:
        return ""
    
    # Remove extra whitespace and normalize
    text = re.sub(r'\s+', ' ', text.strip())
    
    # Remove common HTML entities
    html_entities = {
        '&amp;': '&',
        '&lt;': '<',
        '&gt;': '>',
        '&quot;': '"',
        '&apos;': "'",
        '&nbsp;': ' ',
    }
    
    for entity, replacement in html_entities.items():
        text = text.replace(entity, replacement)
    
    return text


def parse_price(price_text: str) -> Optional[Decimal]:
    """Parse price from text, handling various formats."""
    if not price_text:
        return None
    
    # Clean the price text
    price_text = clean_text(price_text)
    
    # Remove currency symbols and common prefixes
    price_text = re.sub(r'[$£€¥]', '', price_text)
    price_text = re.sub(r'(?:price|cost|was|now|sale):\s*', '', price_text, flags=re.IGNORECASE)
    
    # Extract numeric value with optional decimal
    price_match = re.search(r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', price_text)
    if not price_match:
        return None
    
    try:
        # Remove commas and convert to Decimal
        price_str = price_match.group(1).replace(',', '')
        return Decimal(price_str)
    except (InvalidOperation, ValueError):
        return None


def clean_price(price: Union[str, Decimal, float, int]) -> Optional[Decimal]:
    """Clean and normalize a price value."""
    if price is None:
        return None
    
    if isinstance(price, Decimal):
        return price
    
    if isinstance(price, (int, float)):
        try:
            return Decimal(str(price))
        except (InvalidOperation, ValueError):
            return None
    
    if isinstance(price, str):
        return parse_price(price)
    
    return None


def extract_brand_from_title(title: str) -> Optional[str]:
    """Extract brand name from product title."""
    if not title:
        return None

    title = clean_text(title)

    words = title.split()
    if not words:
        return None

    stopwords = {
        'the', 'new', 'best', 'top', 'pro', 'elite', 'youth', 'kid', 'kids', 'jr', 'junior'
    }

    first_word = re.sub(r"[^A-Za-z]", "", words[0])
    if first_word and first_word.lower() not in stopwords:
        # Preserve original casing of the word in the title
        return words[0]

    # Fall back to searching for an uppercase brand name anywhere in the title
    match = re.search(r"\b([A-Z]{2,})\b", title)
    if match and match.group(1).lower() not in stopwords:
        return match.group(1)

    return None


def parse_sizes(size_text: str) -> List[str]:
    """Parse size information from text."""
    if not size_text:
        return []
    
    size_text = clean_text(size_text)
    
    # Common size patterns
    size_patterns = [
        r'\b([A-Z]+\d*)\b',  # Letter sizes (S, M, L, XL, etc.)
        r'\b(\d+(?:\.\d+)?)\b',  # Numeric sizes
        r'\b(Y[A-Z]+)\b',  # Youth sizes (YS, YM, YL, etc.)
        r'\b(JR|JUNIOR)\b',  # Junior sizes
        r'\b(KIDS?|BOY|GIRL)\b',  # Kids sizes
        r'\b(\d+-\d+)\b',  # Size ranges (10-12, etc.)
    ]
    
    sizes = []
    for pattern in size_patterns:
        matches = re.findall(pattern, size_text, re.IGNORECASE)
        sizes.extend(matches)
    
    # Remove duplicates and normalize
    unique_sizes = list(set(size.upper() for size in sizes))
    return sorted(unique_sizes, key=lambda x: (len(x), x))


def normalize_size(size: str) -> str:
    """Normalize size string to standard format."""
    if not size:
        return ""
    
    size = size.strip().upper()
    
    # Common size mappings
    size_mappings = {
        'XS': 'XS',
        'S': 'S', 
        'M': 'M',
        'L': 'L',
        'XL': 'XL',
        'XXL': 'XXL',
        'XXXL': 'XXXL',
        'YS': 'YS',
        'YM': 'YM', 
        'YL': 'YL',
        'YXL': 'YXL',
        'YXXL': 'YXXL',
        'JR': 'JR',
        'JUNIOR': 'JR',
        'KIDS': 'KIDS',
        'KID': 'KIDS',
        'BOY': 'BOY',
        'BOYS': 'BOY',
        'GIRL': 'GIRL',
        'GIRLS': 'GIRL',
    }
    
    return size_mappings.get(size, size)


def detect_youth_keywords(text: str) -> bool:
    """Detect if text contains youth-related keywords."""
    if not text:
        return False
    
    text = clean_text(text).lower()
    
    youth_keywords = [
        'youth', 'jr', 'junior', 'kids', 'kid', 'boy', 'boys', 'girl', 'girls',
        'child', 'children', 'toddler', 'infant', 'baby', 'little', 'small',
        'ys', 'ym', 'yl', 'yxl', 'yxxl',  # Youth size codes
    ]
    
    adult_keywords = [
        'adult', 'men', 'mens', 'women', 'womens', 'man', 'woman',
        'grown', 'mature', 'senior',
    ]
    
    # Check for adult keywords first (strong negative signal)
    if any(keyword in text for keyword in adult_keywords):
        return False
    
    # Check for youth keywords
    return any(keyword in text for keyword in youth_keywords)


def extract_json_ld(html: str) -> List[Dict[str, Any]]:
    """Extract JSON-LD structured data from HTML."""
    if not html:
        return []

    extractor = _JSONLDScriptExtractor()
    extractor.feed(html)

    json_ld_data: List[Dict[str, Any]] = []
    for script_content in extractor.scripts:
        try:
            data = json.loads(script_content)
        except (json.JSONDecodeError, ValueError):
            continue

        if isinstance(data, list):
            json_ld_data.extend(item for item in data if isinstance(item, dict))
        elif isinstance(data, dict):
            json_ld_data.append(data)

    return json_ld_data


def extract_product_data_from_json_ld(json_ld_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Extract product data from JSON-LD structured data."""
    product_data = {}
    
    for item in json_ld_data:
        if item.get('@type') == 'Product':
            # Extract basic product information
            if 'name' in item:
                product_data['title'] = item['name']
            
            if 'brand' in item:
                if isinstance(item['brand'], dict):
                    product_data['brand'] = item['brand'].get('name', '')
                else:
                    product_data['brand'] = str(item['brand'])
            
            if 'sku' in item:
                product_data['sku'] = item['sku']
            
            if 'mpn' in item:
                product_data['mpn'] = item['mpn']
            
            if 'gtin' in item:
                product_data['gtin'] = item['gtin']
            
            if 'image' in item:
                images = item['image']
                if isinstance(images, list) and images:
                    product_data['image_url'] = images[0]
                elif isinstance(images, str):
                    product_data['image_url'] = images
            
            # Extract offers (pricing)
            if 'offers' in item:
                offers = item['offers']
                if isinstance(offers, list) and offers:
                    offer = offers[0]
                else:
                    offer = offers
                
                if isinstance(offer, dict):
                    if 'price' in offer:
                        product_data['price'] = clean_price(offer['price'])
                    
                    if 'priceCurrency' in offer:
                        product_data['currency'] = offer['priceCurrency']
                    
                    if 'availability' in offer:
                        availability = offer['availability']
                        if 'InStock' in availability:
                            product_data['in_stock'] = True
                        elif 'OutOfStock' in availability:
                            product_data['in_stock'] = False
            
            break  # Use first Product found
    
    return product_data


def normalize_url(url: str, base_url: str) -> str:
    """Normalize and make URL absolute."""
    if not url:
        return ""
    
    # Handle relative URLs
    if url.startswith('//'):
        url = 'https:' + url
    elif url.startswith('/'):
        url = urljoin(base_url, url)
    elif not url.startswith(('http://', 'https://')):
        url = urljoin(base_url, url)
    
    return url


def extract_domain(url: str) -> str:
    """Extract domain from URL."""
    try:
        parsed = urlparse(url)
        return parsed.netloc.lower()
    except Exception:
        return ""


def clean_sku(sku: str) -> Optional[str]:
    """Clean and validate SKU."""
    if not sku:
        return None
    
    sku = clean_text(sku).strip()
    
    # Remove common prefixes
    sku = re.sub(r'^(sku|item|product)[:\s]*', '', sku, flags=re.IGNORECASE)
    
    # Must be alphanumeric with some special chars
    if re.match(r'^[A-Za-z0-9\-_\.]+$', sku) and len(sku) >= 2:
        return sku.upper()
    
    return None


def extract_coupon_code(text: str) -> Optional[str]:
    """Extract coupon code from text."""
    if not text:
        return None
    
    text = clean_text(text)
    normalized = text.upper()

    # Common coupon patterns in uppercase form
    coupon_patterns = [
        r'(?:CODE|COUPON)[\s:]*((?=[A-Z0-9]*\d)[A-Z0-9]{3,20})',
        r'((?=[A-Z0-9]*\d)[A-Z0-9]{3,20})\s+(?:OFF|DISCOUNT)',
        r'SAVE\s+(?:WITH\s+CODE\s+)?((?=[A-Z0-9]*\d)[A-Z0-9]{3,20})',
        r'USE\s+CODE\s+((?=[A-Z0-9]*\d)[A-Z0-9]{3,20})',
    ]

    for pattern in coupon_patterns:
        match = re.search(pattern, normalized)
        if match:
            return match.group(1)

    return None


def parse_promotion_end(text: str) -> Optional[str]:
    """Parse promotion end date from text."""
    if not text:
        return None
    
    text = clean_text(text)
    
    # Common end date patterns
    end_patterns = [
        r'ends?\s+(?:on\s+)?(\w+\s+\d{1,2}(?:st|nd|rd|th)?)',
        r'expires?\s+(?:on\s+)?(\w+\s+\d{1,2}(?:st|nd|rd|th)?)',
        r'valid\s+until\s+(\w+\s+\d{1,2}(?:st|nd|rd|th)?)',
        r'through\s+(\w+\s+\d{1,2}(?:st|nd|rd|th)?)',
    ]
    
    for pattern in end_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)
    
    return None
