"""Pydantic models for sports deals data validation and serialization."""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Union
from urllib.parse import urljoin, urlparse

from pydantic import BaseModel, Field, HttpUrl, computed_field, field_validator


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


class Deal(BaseModel):
    """Core deal model with comprehensive product and pricing information."""
    
    # Core identifiers
    id: str = Field(..., description="Stable hash of canonical_url + sku or gtin")
    title: str = Field(..., min_length=1, max_length=500)
    brand: Optional[str] = Field(None, max_length=100)
    
    # Product classification
    sport: Optional[Sport] = None
    category: Optional[Category] = None
    youth_flag: bool = Field(False, description="Derived from sizing/keywords")
    size_type: SizeType = Field(SizeType.UNKNOWN, description="Detected size type")
    
    # Sizing information
    sizes: Optional[List[str]] = Field(None, description="Available sizes")
    size_range: Optional[str] = Field(None, description="Human-readable size range")
    age_range: Optional[str] = Field(None, description="Age range if specified")
    
    # Pricing
    msrp: Optional[Decimal] = Field(None, ge=0, description="Manufacturer's suggested retail price")
    price: Decimal = Field(..., ge=0, description="Current selling price")
    currency: Currency = Field(Currency.USD)
    
    # Computed pricing fields
    @computed_field
    @property
    def discount_pct(self) -> Optional[float]:
        """Calculate discount percentage if MSRP is available."""
        if self.msrp and self.msrp > 0:
            return float((self.msrp - self.price) / self.msrp * 100)
        return None
    
    @computed_field
    @property
    def savings_amount(self) -> Optional[Decimal]:
        """Calculate absolute savings amount."""
        if self.msrp:
            return self.msrp - self.price
        return None
    
    # Promotion details
    coupon_code: Optional[str] = Field(None, max_length=50)
    ends_at: Optional[datetime] = Field(None, description="Promotion end date if known")
    promotion_type: Optional[str] = Field(None, description="Sale, clearance, etc.")
    
    # Retailer information
    retailer: str = Field(..., min_length=1, max_length=100)
    sku: Optional[str] = Field(None, max_length=100)
    mpn: Optional[str] = Field(None, max_length=100, description="Manufacturer part number")
    gtin: Optional[str] = Field(None, max_length=20, description="Global Trade Item Number")
    
    # URLs and media
    image_url: Optional[HttpUrl] = None
    canonical_url: HttpUrl = Field(..., description="Direct product URL")
    
    # Availability
    in_stock: Optional[bool] = None
    stock_level: Optional[str] = Field(None, description="Limited, in stock, etc.")
    shipping_notes: Optional[str] = Field(None, max_length=200)
    
    # Metadata
    last_seen: datetime = Field(default_factory=datetime.utcnow)
    first_seen: Optional[datetime] = None
    source_url: Optional[HttpUrl] = Field(None, description="URL where deal was found")
    
    # Scoring and ranking
    score: Optional[float] = Field(None, ge=0, le=100, description="Composite quality score")
    relevance_score: Optional[float] = Field(None, ge=0, le=100, description="Youth relevance score")
    
    # Deduplication
    alternate_retailers: Optional[List[str]] = Field(None, description="Other retailers with same product")
    is_duplicate: bool = Field(False, description="Marked as duplicate of another deal")
    canonical_deal_id: Optional[str] = Field(None, description="ID of canonical deal if duplicate")
    
    @field_validator('canonical_url')
    @classmethod
    def validate_canonical_url(cls, v: HttpUrl) -> HttpUrl:
        """Ensure canonical URL is absolute."""
        if not v.scheme or not v.netloc:
            raise ValueError("Canonical URL must be absolute")
        return v
    
    @field_validator('image_url')
    @classmethod
    def validate_image_url(cls, v: Optional[HttpUrl]) -> Optional[HttpUrl]:
        """Ensure image URL is absolute if provided."""
        if v and (not v.scheme or not v.netloc):
            raise ValueError("Image URL must be absolute")
        return v
    
    @field_validator('sizes')
    @classmethod
    def validate_sizes(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Clean and validate size list."""
        if v:
            # Remove empty strings and normalize
            cleaned = [size.strip().upper() for size in v if size.strip()]
            return cleaned if cleaned else None
        return v
    
    def model_post_init(self, __context: Any) -> None:
        """Post-initialization processing."""
        # Set first_seen if not provided
        if self.first_seen is None:
            self.first_seen = self.last_seen
        
        # Generate stable ID if not provided
        if not self.id:
            self.id = self._generate_id()
    
    def _generate_id(self) -> str:
        """Generate a stable ID from product identifiers."""
        import hashlib
        
        # Use the most specific identifier available
        identifier = None
        if self.gtin:
            identifier = f"gtin:{self.gtin}"
        elif self.mpn:
            identifier = f"mpn:{self.mpn}"
        elif self.sku:
            identifier = f"sku:{self.sku}"
        else:
            # Fallback to URL + title hash
            identifier = f"url:{self.canonical_url}:{self.title}"
        
        return hashlib.sha256(identifier.encode()).hexdigest()[:16]
    
    def is_youth_sized(self) -> bool:
        """Determine if this is a youth-sized product."""
        if self.youth_flag:
            return True
        
        if not self.sizes:
            return False
        
        # Check for youth size indicators
        youth_indicators = {
            'Y', 'YS', 'YM', 'YL', 'YXL', 'YXXL',  # Youth letter sizes
            'JR', 'JUNIOR',  # Junior sizes
            'KIDS', 'KID',  # Kids sizes
            'BOY', 'BOYS', 'GIRL', 'GIRLS',  # Gender-specific youth
        }
        
        for size in self.sizes:
            if any(indicator in size.upper() for indicator in youth_indicators):
                return True
        
        # Check for numeric youth sizes (typically 1-6 for shoes, etc.)
        try:
            numeric_sizes = [float(s) for s in self.sizes if s.replace('.', '').isdigit()]
            if numeric_sizes and all(1 <= size <= 6 for size in numeric_sizes):
                return True
        except (ValueError, TypeError):
            pass
        
        return False
    
    def get_effective_price(self) -> Decimal:
        """Get the effective price after any coupon discounts."""
        # This would be enhanced with coupon logic in a real implementation
        return self.price
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with proper serialization."""
        return self.model_dump(mode='json', exclude_none=True)


class RetailerConfig(BaseModel):
    """Configuration for a retailer source."""
    
    name: str = Field(..., min_length=1, max_length=100)
    base_url: HttpUrl
    enabled: bool = Field(True)
    
    # Scraping configuration
    selectors: Dict[str, str] = Field(..., description="CSS selectors for data extraction")
    pagination: Optional[Dict[str, Any]] = Field(None, description="Pagination configuration")
    
    # Product classification
    sport: Optional[Sport] = None
    category_hints: Optional[List[Category]] = None
    youth_keywords: Optional[List[str]] = Field(None, description="Keywords indicating youth products")
    
    # Rate limiting
    rate_limit: Dict[str, int] = Field(
        default_factory=lambda: {"requests_per_minute": 10, "burst": 3}
    )
    
    # Additional settings
    requires_js: bool = Field(False, description="Whether JavaScript rendering is required")
    user_agent: Optional[str] = None
    headers: Optional[Dict[str, str]] = None
    
    # Validation
    min_items_per_page: int = Field(1, ge=1)
    max_pages: int = Field(50, ge=1, le=1000)
    timeout_seconds: int = Field(30, ge=5, le=300)


class ScrapingSession(BaseModel):
    """Metadata for a scraping session."""
    
    session_id: str = Field(..., description="Unique session identifier")
    retailer: str = Field(..., description="Retailer name")
    started_at: datetime = Field(default_factory=datetime.utcnow)
    ended_at: Optional[datetime] = None
    
    # Statistics
    pages_scraped: int = Field(0, ge=0)
    items_found: int = Field(0, ge=0)
    items_parsed: int = Field(0, ge=0)
    errors: int = Field(0, ge=0)
    
    # Status
    status: Literal["running", "completed", "failed", "cancelled"] = "running"
    error_message: Optional[str] = None
    
    @computed_field
    @property
    def duration_seconds(self) -> Optional[float]:
        """Calculate session duration in seconds."""
        if self.ended_at:
            return (self.ended_at - self.started_at).total_seconds()
        return None
    
    @computed_field
    @property
    def success_rate(self) -> float:
        """Calculate parsing success rate."""
        if self.items_found == 0:
            return 0.0
        return (self.items_parsed / self.items_found) * 100


class NewsletterConfig(BaseModel):
    """Configuration for newsletter generation."""
    
    title: str = Field("Youth Sports Gear Deals", max_length=200)
    subtitle: Optional[str] = Field(None, max_length=300)
    
    # Content settings
    top_per_sport: int = Field(8, ge=1, le=50)
    min_discount_pct: float = Field(20.0, ge=0, le=100)
    max_deals_total: int = Field(100, ge=1, le=500)
    
    # Grouping
    group_by_sport: bool = Field(True)
    group_by_category: bool = Field(True)
    show_youth_only: bool = Field(True)
    
    # Styling
    theme: Literal["light", "dark", "auto"] = "light"
    include_images: bool = Field(True)
    include_coupons: bool = Field(True)
    
    # Output
    formats: List[Literal["html", "markdown"]] = Field(default_factory=lambda: ["html", "markdown"])
    output_dir: str = Field("out", description="Output directory for generated newsletters")


class PriceHistory(BaseModel):
    """Price history tracking for a deal."""
    
    deal_id: str = Field(..., description="Reference to deal ID")
    price: Decimal = Field(..., ge=0)
    msrp: Optional[Decimal] = Field(None, ge=0)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    retailer: str = Field(..., description="Retailer where price was observed")
    
    # Additional context
    stock_status: Optional[str] = None
    promotion_active: bool = Field(False)
    notes: Optional[str] = Field(None, max_length=200)


# Type aliases for common use cases
DealList = List[Deal]
RetailerConfigList = List[RetailerConfig]
PriceHistoryList = List[PriceHistory]
