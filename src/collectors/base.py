"""Base collector class with common functionality for all retailers."""

import asyncio
import hashlib
import time
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urljoin, urlparse

import httpx
import structlog
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from selectolax.parser import HTMLParser

from ..models import Deal, RetailerConfig, ScrapingSession
from ..utils.parsing import (
    clean_text,
    extract_json_ld,
    extract_product_data_from_json_ld,
    normalize_url,
    parse_price,
    detect_youth_keywords,
)
from ..utils.validation import validate_url

logger = structlog.get_logger()


class CollectorError(Exception):
    """Base exception for collector errors."""
    pass


class RateLimitError(CollectorError):
    """Raised when rate limit is exceeded."""
    pass


class BaseCollector(ABC):
    """Base class for all retailer collectors."""
    
    def __init__(self, config: RetailerConfig):
        """Initialize collector with configuration."""
        self.config = config
        self.session_id = self._generate_session_id()
        self.session = ScrapingSession(
            session_id=self.session_id,
            retailer=config.name,
            started_at=datetime.utcnow()
        )
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.client: Optional[httpx.AsyncClient] = None
        
        # Rate limiting
        self.request_times: List[float] = []
        self.requests_per_minute = config.rate_limit.get('requests_per_minute', 10)
        self.burst_limit = config.rate_limit.get('burst', 3)
        
        # Statistics
        self.pages_scraped = 0
        self.items_found = 0
        self.items_parsed = 0
        self.errors = 0
    
    def _generate_session_id(self) -> str:
        """Generate unique session ID."""
        timestamp = datetime.utcnow().isoformat()
        data = f"{self.config.name}_{timestamp}"
        return hashlib.md5(data.encode()).hexdigest()[:12]
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self._setup_browser()
        await self._setup_http_client()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self._cleanup()
    
    async def _setup_browser(self) -> None:
        """Set up Playwright browser for JavaScript rendering."""
        if not self.config.requires_js:
            return
        
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-dev-shm-usage']
        )
        
        self.context = await self.browser.new_context(
            user_agent=self.config.user_agent or (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            viewport={'width': 1920, 'height': 1080}
        )
        
        self.page = await self.context.new_page()
    
    async def _setup_http_client(self) -> None:
        """Set up HTTP client for API requests."""
        headers = {
            'User-Agent': self.config.user_agent or (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        }
        
        if self.config.headers:
            headers.update(self.config.headers)
        
        self.client = httpx.AsyncClient(
            headers=headers,
            timeout=self.config.timeout_seconds,
            follow_redirects=True
        )
    
    async def _cleanup(self) -> None:
        """Clean up resources."""
        if self.client:
            await self.client.aclose()
        
        if self.context:
            await self.context.close()
        
        if self.browser:
            await self.browser.close()
        
        # Update session statistics
        self.session.ended_at = datetime.utcnow()
        self.session.pages_scraped = self.pages_scraped
        self.session.items_found = self.items_found
        self.session.items_parsed = self.items_parsed
        self.session.errors = self.errors
        self.session.status = "completed" if self.errors == 0 else "failed"
    
    async def _rate_limit(self) -> None:
        """Enforce rate limiting."""
        now = time.time()
        
        # Remove requests older than 1 minute
        self.request_times = [t for t in self.request_times if now - t < 60]
        
        # Check if we're at the limit
        if len(self.request_times) >= self.requests_per_minute:
            sleep_time = 60 - (now - self.request_times[0])
            if sleep_time > 0:
                logger.info(f"Rate limit reached, sleeping for {sleep_time:.1f}s")
                await asyncio.sleep(sleep_time)
        
        # Check burst limit
        recent_requests = [t for t in self.request_times if now - t < 10]
        if len(recent_requests) >= self.burst_limit:
            sleep_time = 10 - (now - recent_requests[0])
            if sleep_time > 0:
                logger.info(f"Burst limit reached, sleeping for {sleep_time:.1f}s")
                await asyncio.sleep(sleep_time)
        
        self.request_times.append(now)
    
    async def fetch_page(self, url: str) -> str:
        """Fetch page content with rate limiting and error handling."""
        await self._rate_limit()
        
        if not validate_url(url):
            raise CollectorError(f"Invalid URL: {url}")
        
        try:
            if self.config.requires_js and self.page:
                # Use Playwright for JavaScript rendering
                response = await self.page.goto(url, wait_until='networkidle')
                if not response or response.status >= 400:
                    raise CollectorError(f"HTTP {response.status if response else 'unknown'}: {url}")
                content = await self.page.content()
            else:
                # Use HTTP client for simple requests
                response = await self.client.get(url)
                response.raise_for_status()
                content = response.text
            
            self.pages_scraped += 1
            logger.info(f"Fetched page: {url}")
            return content
            
        except httpx.HTTPStatusError as e:
            self.errors += 1
            if e.response.status_code == 429:
                raise RateLimitError(f"Rate limited by {url}")
            raise CollectorError(f"HTTP {e.response.status_code}: {url}")
        except Exception as e:
            self.errors += 1
            raise CollectorError(f"Failed to fetch {url}: {str(e)}")
    
    def parse_item(self, item_html: str, source_url: str) -> Optional[Deal]:
        """Parse a single item from HTML."""
        try:
            self.items_found += 1
            
            # Extract basic data using selectors
            deal_data = self._extract_basic_data(item_html, source_url)
            if not deal_data:
                return None
            
            # Try to extract JSON-LD data for additional information
            json_ld_data = extract_json_ld(item_html)
            if json_ld_data:
                json_ld_product = extract_product_data_from_json_ld(json_ld_data)
                deal_data.update(json_ld_product)
            
            # Apply retailer-specific parsing
            deal_data = self._parse_item_specific(item_html, deal_data)
            
            # Validate and create Deal object
            deal = self._create_deal(deal_data)
            if deal:
                self.items_parsed += 1
                logger.debug(f"Parsed deal: {deal.title}")
            
            return deal
            
        except Exception as e:
            self.errors += 1
            logger.error(f"Error parsing item: {str(e)}")
            return None
    
    def _extract_basic_data(self, item_html: str, source_url: str) -> Optional[Dict[str, Any]]:
        """Extract basic data using CSS selectors."""
        parser = HTMLParser(item_html)
        
        # Extract required fields
        title_elem = parser.css_first(self.config.selectors.get('title', ''))
        if not title_elem:
            return None
        
        title = clean_text(title_elem.text())
        if not title:
            return None
        
        # Extract price
        price_elem = parser.css_first(self.config.selectors.get('price', ''))
        if not price_elem:
            return None
        
        price = parse_price(price_elem.text())
        if not price:
            return None
        
        # Extract URL
        url_elem = parser.css_first(self.config.selectors.get('url', ''))
        if not url_elem:
            return None
        
        product_url = url_elem.attributes.get('href', '')
        if not product_url:
            return None
        
        canonical_url = normalize_url(product_url, str(self.config.base_url))
        
        # Extract optional fields
        msrp = None
        msrp_elem = parser.css_first(self.config.selectors.get('msrp', ''))
        if msrp_elem:
            msrp = parse_price(msrp_elem.text())
        
        # Extract image
        image_url = None
        image_elem = parser.css_first(self.config.selectors.get('image', ''))
        if image_elem:
            image_src = image_elem.attributes.get('src', '')
            if image_src:
                image_url = normalize_url(image_src, str(self.config.base_url))
        
        # Extract brand from title if not found elsewhere
        brand = self._extract_brand(parser, title)
        
        # Detect youth keywords
        youth_flag = self._detect_youth_keywords(title, parser)
        
        # Extract sizes
        sizes = self._extract_sizes(parser)
        
        return {
            'title': title,
            'price': price,
            'msrp': msrp,
            'canonical_url': canonical_url,
            'image_url': image_url,
            'brand': brand,
            'youth_flag': youth_flag,
            'sizes': sizes,
            'retailer': self.config.name,
            'source_url': source_url,
            'sport': self.config.sport.value if self.config.sport else None,
        }
    
    def _extract_brand(self, parser: HTMLParser, title: str) -> Optional[str]:
        """Extract brand from HTML or title."""
        # Try brand selector first
        brand_elem = parser.css_first(self.config.selectors.get('brand', ''))
        if brand_elem:
            brand = clean_text(brand_elem.text())
            if brand:
                return brand
        
        # Fall back to extracting from title
        from ..utils.parsing import extract_brand_from_title
        return extract_brand_from_title(title)
    
    def _detect_youth_keywords(self, title: str, parser: HTMLParser) -> bool:
        """Detect youth keywords in title and other elements."""
        # Check title
        if detect_youth_keywords(title):
            return True
        
        # Check youth keywords from config
        if self.config.youth_keywords:
            title_lower = title.lower()
            if any(keyword.lower() in title_lower for keyword in self.config.youth_keywords):
                return True
        
        # Check other elements for youth indicators
        for selector in ['description', 'category', 'breadcrumb']:
            elem = parser.css_first(self.config.selectors.get(selector, ''))
            if elem and detect_youth_keywords(elem.text()):
                return True
        
        return False
    
    def _extract_sizes(self, parser: HTMLParser) -> Optional[List[str]]:
        """Extract available sizes."""
        sizes_elem = parser.css_first(self.config.selectors.get('sizes', ''))
        if not sizes_elem:
            return None
        
        sizes_text = sizes_elem.text()
        if not sizes_text:
            return None
        
        from ..utils.parsing import parse_sizes
        sizes = parse_sizes(sizes_text)
        return sizes if sizes else None
    
    def _create_deal(self, deal_data: Dict[str, Any]) -> Optional[Deal]:
        """Create Deal object from extracted data."""
        try:
            # Generate stable ID
            deal_data['id'] = self._generate_deal_id(deal_data)
            
            # Set first_seen if not provided
            if 'first_seen' not in deal_data:
                deal_data['first_seen'] = datetime.utcnow()
            
            return Deal(**deal_data)
        except Exception as e:
            logger.error(f"Error creating deal: {str(e)}")
            return None
    
    def _generate_deal_id(self, deal_data: Dict[str, Any]) -> str:
        """Generate stable ID for deal."""
        # Use GTIN if available
        if deal_data.get('gtin'):
            return f"gtin:{deal_data['gtin']}"
        
        # Use MPN if available
        if deal_data.get('mpn'):
            return f"mpn:{deal_data['mpn']}"
        
        # Use SKU if available
        if deal_data.get('sku'):
            return f"sku:{deal_data['sku']}"
        
        # Fall back to URL + title hash
        url = deal_data.get('canonical_url', '')
        title = deal_data.get('title', '')
        data = f"{url}:{title}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]
    
    @abstractmethod
    def _parse_item_specific(self, item_html: str, deal_data: Dict[str, Any]) -> Dict[str, Any]:
        """Retailer-specific parsing logic. Must be implemented by subclasses."""
        pass
    
    @abstractmethod
    async def collect_deals(self) -> List[Deal]:
        """Collect all deals from the retailer. Must be implemented by subclasses."""
        pass
    
    async def collect_deals_with_pagination(self) -> List[Deal]:
        """Collect deals with pagination support."""
        all_deals = []
        
        if not self.config.pagination:
            # Single page collection
            content = await self.fetch_page(str(self.config.base_url))
            deals = self._parse_deals_from_page(content, str(self.config.base_url))
            all_deals.extend(deals)
        else:
            # Paginated collection
            page_num = self.config.pagination.get('start', 1)
            max_pages = self.config.pagination.get('max_pages', 10)
            
            while page_num <= max_pages:
                try:
                    page_url = self._build_page_url(page_num)
                    content = await self.fetch_page(page_url)
                    deals = self._parse_deals_from_page(content, page_url)
                    
                    if not deals:
                        logger.info(f"No deals found on page {page_num}, stopping pagination")
                        break
                    
                    all_deals.extend(deals)
                    page_num += 1
                    
                    # Check if we have enough items
                    if len(deals) < self.config.min_items_per_page:
                        logger.info(f"Page {page_num} has fewer than {self.config.min_items_per_page} items, stopping")
                        break
                        
                except Exception as e:
                    logger.error(f"Error fetching page {page_num}: {str(e)}")
                    break
        
        logger.info(f"Collected {len(all_deals)} deals from {self.config.name}")
        return all_deals
    
    def _build_page_url(self, page_num: int) -> str:
        """Build URL for specific page number."""
        base_url = str(self.config.base_url)
        pagination = self.config.pagination
        
        if pagination['type'] == 'page_param':
            param = pagination['param']
            if '?' in base_url:
                return f"{base_url}&{param}={page_num}"
            else:
                return f"{base_url}?{param}={page_num}"
        elif pagination['type'] == 'offset':
            limit = pagination['limit']
            offset = (page_num - 1) * limit
            if '?' in base_url:
                return f"{base_url}&offset={offset}&limit={limit}"
            else:
                return f"{base_url}?offset={offset}&limit={limit}"
        else:
            raise CollectorError(f"Unsupported pagination type: {pagination['type']}")
    
    def _parse_deals_from_page(self, content: str, source_url: str) -> List[Deal]:
        """Parse all deals from a page."""
        parser = HTMLParser(content)
        item_selectors = self.config.selectors.get('item', '')
        
        if not item_selectors:
            raise CollectorError("No item selector configured")
        
        item_elements = parser.css(item_selectors)
        deals = []
        
        for item_elem in item_elements:
            item_html = item_elem.html
            deal = self.parse_item(item_html, source_url)
            if deal:
                deals.append(deal)
        
        return deals
