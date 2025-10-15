"""Lightweight data models used throughout the project.

The original project used Pydantic for validation and serialisation.  The
execution environment available to the kata does not allow installing
third-party dependencies which caused the application to crash immediately
with ``ModuleNotFoundError: No module named 'pydantic'``.  To keep the public
API identical for the rest of the codebase and the accompanying tests, this
module now provides small dataclass based replacements that implement the
behaviour we rely on from Pydantic.

Only a tiny subset of Pydantic's features are required: type coercion for a few
fields, URL validation, automatic ID generation and convenient conversion to a
serialisable ``dict``.  Reimplementing those features locally keeps the rest of
the project untouched while ensuring the scraper can run in a minimal Python
environment with no external packages installed.
"""

from __future__ import annotations

from dataclasses import dataclass, field, fields
from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from enum import Enum
from typing import Any, Dict, List, Literal, Optional
from urllib.parse import urlparse


class Sport(str, Enum):
    """Supported sports categories."""
    SOCCER = "soccer"
    BASKETBALL = "basketball"
    HOCKEY = "hockey"
    LACROSSE = "lacrosse"
    TENNIS = "tennis"
    BASEBALL = "baseball"
    SOFTBALL = "softball"
    RUNNING = "running"
    FOOTBALL = "football"
    MULTI = "multi"


class Category(str, Enum):
    """Product categories."""
    FOOTWEAR = "footwear"
    APPAREL = "apparel"
    PROTECTIVE = "protective"
    EQUIPMENT = "equipment"
    BAGS = "bags"
    ACCESSORIES = "accessories"


class Currency(str, Enum):
    """Supported currencies."""
    USD = "USD"


class SizeType(str, Enum):
    """Size type classifications."""
    YOUTH = "youth"
    JUNIOR = "junior"
    ADULT = "adult"
    UNKNOWN = "unknown"


def _coerce_decimal(value: Any, *, field_name: str) -> Decimal:
    """Coerce the provided value to :class:`~decimal.Decimal`.

    Raises
    ------
    ValueError
        If the value cannot be interpreted as a non-negative decimal number.
    """

    if isinstance(value, Decimal):
        return value

    try:
        decimal_value = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError(f"Invalid decimal value for {field_name}: {value!r}") from exc

    if decimal_value < 0:
        raise ValueError(f"{field_name} must be non-negative")

    return decimal_value


def _optional_decimal(value: Optional[Any], *, field_name: str) -> Optional[Decimal]:
    """Coerce an optional decimal value."""

    if value is None:
        return None
    return _coerce_decimal(value, field_name=field_name)


def _validate_url(value: Optional[str], *, field_name: str, required: bool = False) -> Optional[str]:
    """Validate that a URL is absolute."""

    if not value:
        if required:
            raise ValueError(f"{field_name} is required")
        return None

    parsed = urlparse(str(value))
    if not parsed.scheme or not parsed.netloc:
        raise ValueError(f"{field_name} must be an absolute URL")
    return str(value)


def _clean_sizes(sizes: Optional[List[str]]) -> Optional[List[str]]:
    """Normalise size values by stripping whitespace and upper casing."""

    if not sizes:
        return None

    cleaned = [size.strip().upper() for size in sizes if size and size.strip()]
    return cleaned or None


def _decimal_to_str(value: Decimal) -> str:
    """Serialise a decimal value to a fixed-point string."""

    quantized = value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return format(quantized, "f")


@dataclass
class Deal:
    """Core deal model with comprehensive product and pricing information."""

    title: str
    price: Decimal
    retailer: str
    canonical_url: str
    id: Optional[str] = None
    brand: Optional[str] = None
    sport: Optional[Sport] = None
    category: Optional[Category] = None
    youth_flag: bool = False
    size_type: SizeType = SizeType.UNKNOWN
    sizes: Optional[List[str]] = None
    size_range: Optional[str] = None
    age_range: Optional[str] = None
    msrp: Optional[Decimal] = None
    currency: Currency = Currency.USD
    coupon_code: Optional[str] = None
    ends_at: Optional[datetime] = None
    promotion_type: Optional[str] = None
    sku: Optional[str] = None
    mpn: Optional[str] = None
    gtin: Optional[str] = None
    image_url: Optional[str] = None
    in_stock: Optional[bool] = None
    stock_level: Optional[str] = None
    shipping_notes: Optional[str] = None
    last_seen: datetime = field(default_factory=datetime.utcnow)
    first_seen: Optional[datetime] = None
    source_url: Optional[str] = None
    score: Optional[float] = None
    relevance_score: Optional[float] = None
    alternate_retailers: Optional[List[str]] = None
    is_duplicate: bool = False
    canonical_deal_id: Optional[str] = None

    def __post_init__(self) -> None:
        """Perform validation and normalisation similar to Pydantic."""

        if not self.title:
            raise ValueError("title is required")
        if not self.retailer:
            raise ValueError("retailer is required")

        # Convert enum values from strings if required
        if self.sport and isinstance(self.sport, str):
            self.sport = Sport(self.sport)
        if self.category and isinstance(self.category, str):
            self.category = Category(self.category)
        if isinstance(self.currency, str):
            self.currency = Currency(self.currency)
        if isinstance(self.size_type, str):
            self.size_type = SizeType(self.size_type)

        # Coerce numeric values
        self.price = _coerce_decimal(self.price, field_name="price")
        self.msrp = _optional_decimal(self.msrp, field_name="msrp")

        if self.msrp and self.msrp < self.price:
            # Allow MSRP to be lower than price but do not allow negative discounts.
            self.msrp = self.msrp

        # Validate URLs
        self.canonical_url = _validate_url(self.canonical_url, field_name="canonical_url", required=True)  # type: ignore[assignment]
        self.image_url = _validate_url(self.image_url, field_name="image_url")
        self.source_url = _validate_url(self.source_url, field_name="source_url")

        # Normalise sizes
        self.sizes = _clean_sizes(self.sizes)

        # Ensure first_seen defaults to last_seen
        if self.first_seen is None:
            self.first_seen = self.last_seen

        # Generate ID if missing
        if not self.id:
            self.id = self._generate_id()

    @property
    def discount_pct(self) -> Optional[float]:
        """Calculate discount percentage if MSRP is available."""

        if self.msrp and self.msrp > 0:
            discount = (self.msrp - self.price) / self.msrp * 100
            return float(discount)
        return None

    @property
    def savings_amount(self) -> Optional[Decimal]:
        """Calculate absolute savings amount."""

        if self.msrp:
            return self.msrp - self.price
        return None

    def _generate_id(self) -> str:
        """Generate a stable ID from product identifiers."""

        import hashlib

        identifier: str
        if self.gtin:
            identifier = f"gtin:{self.gtin}"
        elif self.mpn:
            identifier = f"mpn:{self.mpn}"
        elif self.sku:
            identifier = f"sku:{self.sku}"
        else:
            identifier = f"url:{self.canonical_url}:{self.title}"

        return hashlib.sha256(identifier.encode()).hexdigest()[:16]

    def is_youth_sized(self) -> bool:
        """Determine if this is a youth-sized product."""

        if self.youth_flag:
            return True

        if not self.sizes:
            return False

        youth_indicators = {
            "Y",
            "YS",
            "YM",
            "YL",
            "YXL",
            "YXXL",
            "JR",
            "JUNIOR",
            "KIDS",
            "KID",
            "BOY",
            "BOYS",
            "GIRL",
            "GIRLS",
        }

        for size in self.sizes:
            if any(indicator in size for indicator in youth_indicators):
                return True

        try:
            numeric_sizes = [float(s) for s in self.sizes if s.replace(".", "").isdigit()]
            if numeric_sizes and all(1 <= size <= 6 for size in numeric_sizes):
                return True
        except (ValueError, TypeError):
            pass

        return False

    def get_effective_price(self) -> Decimal:
        """Get the effective price after any coupon discounts."""

        return self.price

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with proper serialization."""

        data: Dict[str, Any] = {}
        for field_info in fields(self):
            value = getattr(self, field_info.name)
            if value is None:
                continue

            if isinstance(value, Enum):
                data[field_info.name] = value.value
            elif isinstance(value, Decimal):
                data[field_info.name] = _decimal_to_str(value)
            elif isinstance(value, datetime):
                data[field_info.name] = value.isoformat()
            else:
                data[field_info.name] = value

        if self.discount_pct is not None:
            data["discount_pct"] = round(self.discount_pct, 2)
        if self.savings_amount is not None:
            data["savings_amount"] = _decimal_to_str(self.savings_amount)

        return data


@dataclass
class RetailerConfig:
    """Configuration for a retailer source."""

    name: str
    base_url: str
    selectors: Dict[str, str]
    enabled: bool = True
    pagination: Optional[Dict[str, Any]] = None
    sport: Optional[Sport] = None
    category_hints: Optional[List[Category]] = None
    youth_keywords: Optional[List[str]] = None
    rate_limit: Dict[str, int] = field(default_factory=lambda: {"requests_per_minute": 10, "burst": 3})
    requires_js: bool = False
    user_agent: Optional[str] = None
    headers: Optional[Dict[str, str]] = None
    min_items_per_page: int = 1
    max_pages: int = 50
    timeout_seconds: int = 30

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("name is required")

        self.base_url = _validate_url(self.base_url, field_name="base_url", required=True)  # type: ignore[assignment]

        if self.sport and isinstance(self.sport, str):
            self.sport = Sport(self.sport)

        if self.category_hints:
            self.category_hints = [Category(cat) if isinstance(cat, str) else cat for cat in self.category_hints]

        if self.min_items_per_page < 1:
            raise ValueError("min_items_per_page must be at least 1")

        if not (1 <= self.max_pages <= 1000):
            raise ValueError("max_pages must be between 1 and 1000")

        if not (5 <= self.timeout_seconds <= 300):
            raise ValueError("timeout_seconds must be between 5 and 300")

    def to_dict(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {}
        for field_info in fields(self):
            value = getattr(self, field_info.name)
            if value is None:
                continue
            if isinstance(value, Enum):
                data[field_info.name] = value.value
            elif isinstance(value, list) and value and isinstance(value[0], Enum):
                data[field_info.name] = [item.value for item in value]
            else:
                data[field_info.name] = value
        return data


@dataclass
class ScrapingSession:
    """Metadata for a scraping session."""

    session_id: str
    retailer: str
    started_at: datetime = field(default_factory=datetime.utcnow)
    ended_at: Optional[datetime] = None
    pages_scraped: int = 0
    items_found: int = 0
    items_parsed: int = 0
    errors: int = 0
    status: Literal["running", "completed", "failed", "cancelled"] = "running"
    error_message: Optional[str] = None

    @property
    def duration_seconds(self) -> Optional[float]:
        if self.ended_at:
            return (self.ended_at - self.started_at).total_seconds()
        return None

    @property
    def success_rate(self) -> float:
        if self.items_found == 0:
            return 0.0
        return (self.items_parsed / self.items_found) * 100

    def to_dict(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {}
        for field_info in fields(self):
            value = getattr(self, field_info.name)
            if value is None:
                continue
            if isinstance(value, datetime):
                data[field_info.name] = value.isoformat()
            else:
                data[field_info.name] = value

        if self.duration_seconds is not None:
            data["duration_seconds"] = self.duration_seconds
        data["success_rate"] = self.success_rate

        return data


@dataclass
class NewsletterConfig:
    """Configuration for newsletter generation."""

    title: str = "Youth Sports Gear Deals"
    subtitle: Optional[str] = None
    top_per_sport: int = 8
    min_discount_pct: float = 20.0
    max_deals_total: int = 100
    group_by_sport: bool = True
    group_by_category: bool = True
    show_youth_only: bool = True
    theme: Literal["light", "dark", "auto"] = "light"
    include_images: bool = True
    include_coupons: bool = True
    formats: List[Literal["html", "markdown"]] = field(default_factory=lambda: ["html", "markdown"])
    output_dir: str = "out"

    def __post_init__(self) -> None:
        if self.top_per_sport < 1 or self.top_per_sport > 50:
            raise ValueError("top_per_sport must be between 1 and 50")
        if not (0 <= self.min_discount_pct <= 100):
            raise ValueError("min_discount_pct must be between 0 and 100")
        if self.max_deals_total < 1 or self.max_deals_total > 500:
            raise ValueError("max_deals_total must be between 1 and 500")


@dataclass
class PriceHistory:
    """Price history tracking for a deal."""

    deal_id: str
    price: Decimal
    timestamp: datetime = field(default_factory=datetime.utcnow)
    retailer: str = ""
    msrp: Optional[Decimal] = None
    stock_status: Optional[str] = None
    promotion_active: bool = False
    notes: Optional[str] = None

    def __post_init__(self) -> None:
        self.price = _coerce_decimal(self.price, field_name="price")
        self.msrp = _optional_decimal(self.msrp, field_name="msrp")

    def to_dict(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {}
        for field_info in fields(self):
            value = getattr(self, field_info.name)
            if value is None:
                continue
            if isinstance(value, Decimal):
                data[field_info.name] = _decimal_to_str(value)
            elif isinstance(value, datetime):
                data[field_info.name] = value.isoformat()
            else:
                data[field_info.name] = value
        return data


# Type aliases for common use cases
DealList = List[Deal]
RetailerConfigList = List[RetailerConfig]
PriceHistoryList = List[PriceHistory]

