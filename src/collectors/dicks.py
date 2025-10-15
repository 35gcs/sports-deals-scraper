"""Dick's Sporting Goods collector."""

import re
from typing import Any, Dict, List

from .base import BaseCollector
from ..models import Deal, Sport, Category
from ..utils.parsing import clean_text, parse_price, extract_coupon_code


class DicksCollector(BaseCollector):
    """Collector for Dick's Sporting Goods deals."""
    
    def _parse_item_specific(self, item_html: str, deal_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Dick's-specific data."""
        from selectolax.parser import HTMLParser
        parser = HTMLParser(item_html)
        
        # Extract SKU
        sku_elem = parser.css_first('[data-testid="product-sku"], .product-sku, .sku')
        if sku_elem:
            sku_text = clean_text(sku_elem.text())
            if sku_text:
                deal_data['sku'] = sku_text.replace('SKU:', '').strip()
        
        # Extract product ID from URL or data attributes
        product_link = parser.css_first('a[href*="/product/"]')
        if product_link:
            href = product_link.attributes.get('href', '')
            product_id_match = re.search(r'/product/([^/?]+)', href)
            if product_id_match:
                deal_data['sku'] = product_id_match.group(1)
        
        # Extract brand from brand link or text
        brand_elem = parser.css_first('.brand-link, .product-brand, [data-testid="product-brand"]')
        if brand_elem:
            brand_text = clean_text(brand_elem.text())
            if brand_text:
                deal_data['brand'] = brand_text
        
        # Extract category information
        category_elem = parser.css_first('.breadcrumb, .category-path')
        if category_elem:
            category_text = category_elem.text()
            deal_data['category'] = self._map_category(category_text)
            deal_data['sport'] = self._map_sport(category_text)
        
        # Extract size information
        sizes_elem = parser.css_first('.size-selector, .available-sizes')
        if sizes_elem:
            size_links = sizes_elem.css('a, button')
            sizes = []
            for size_link in size_links:
                size_text = clean_text(size_link.text())
                if size_text and size_text not in ['Select Size', 'Size']:
                    sizes.append(size_text)
            if sizes:
                deal_data['sizes'] = sizes
        
        # Extract stock status
        stock_elem = parser.css_first('.stock-status, .availability')
        if stock_elem:
            stock_text = stock_elem.text().lower()
            if 'in stock' in stock_text:
                deal_data['in_stock'] = True
            elif 'out of stock' in stock_text or 'unavailable' in stock_text:
                deal_data['in_stock'] = False
            elif 'limited' in stock_text:
                deal_data['stock_level'] = 'limited'
        
        # Extract promotion information
        promo_elem = parser.css_first('.promo-badge, .sale-badge, .clearance-badge')
        if promo_elem:
            promo_text = clean_text(promo_elem.text())
            if promo_text:
                deal_data['promotion_type'] = promo_text.lower()
        
        # Extract coupon code if present
        coupon_elem = parser.css_first('.coupon-code, .promo-code')
        if coupon_elem:
            coupon_text = clean_text(coupon_elem.text())
            coupon_code = extract_coupon_code(coupon_text)
            if coupon_code:
                deal_data['coupon_code'] = coupon_code
        
        # Enhanced youth detection for Dick's
        title = deal_data.get('title', '').lower()
        youth_indicators = [
            'youth', 'jr', 'junior', 'kids', 'boy', 'girl', 'child',
            'ys', 'ym', 'yl', 'yxl', 'yxxl',  # Youth sizes
            'little', 'small', 'toddler'
        ]
        
        if any(indicator in title for indicator in youth_indicators):
            deal_data['youth_flag'] = True
        
        # Check for adult indicators
        adult_indicators = ['adult', 'men', 'mens', 'women', 'womens', 'man', 'woman']
        if any(indicator in title for indicator in adult_indicators):
            deal_data['youth_flag'] = False
        
        return deal_data
    
    def _map_category(self, category_text: str) -> str:
        """Map Dick's category text to our category enum."""
        category_text = category_text.lower()
        
        if any(word in category_text for word in ['shoe', 'cleat', 'sneaker', 'boot']):
            return Category.FOOTWEAR.value
        elif any(word in category_text for word in ['shirt', 'jersey', 'pant', 'short', 'jacket', 'hoodie']):
            return Category.APPAREL.value
        elif any(word in category_text for word in ['helmet', 'pad', 'guard', 'protection']):
            return Category.PROTECTIVE.value
        elif any(word in category_text for word in ['ball', 'bat', 'stick', 'racket', 'club']):
            return Category.EQUIPMENT.value
        elif any(word in category_text for word in ['bag', 'backpack', 'duffel']):
            return Category.BAGS.value
        else:
            return Category.ACCESSORIES.value
    
    def _map_sport(self, category_text: str) -> str:
        """Map Dick's category text to our sport enum."""
        category_text = category_text.lower()
        
        if any(word in category_text for word in ['soccer', 'football']):
            return Sport.SOCCER.value
        elif any(word in category_text for word in ['basketball', 'hoop']):
            return Sport.BASKETBALL.value
        elif any(word in category_text for word in ['hockey', 'ice']):
            return Sport.HOCKEY.value
        elif any(word in category_text for word in ['lacrosse', 'lax']):
            return Sport.LACROSSE.value
        elif any(word in category_text for word in ['tennis', 'racquet']):
            return Sport.TENNIS.value
        elif any(word in category_text for word in ['baseball', 'softball']):
            return Sport.BASEBALL.value
        elif any(word in category_text for word in ['running', 'jog']):
            return Sport.RUNNING.value
        elif any(word in category_text for word in ['football', 'gridiron']):
            return Sport.FOOTBALL.value
        else:
            return Sport.MULTI.value
    
    async def collect_deals(self) -> List[Deal]:
        """Collect deals from Dick's Sporting Goods."""
        return await self.collect_deals_with_pagination()
