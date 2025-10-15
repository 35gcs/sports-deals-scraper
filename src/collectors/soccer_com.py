"""Soccer.com collector."""

import re
from typing import Any, Dict, List

from .base import BaseCollector
from ..models import Deal, Sport, Category
from ..utils.parsing import clean_text, parse_price, extract_coupon_code


class SoccerComCollector(BaseCollector):
    """Collector for Soccer.com deals."""
    
    def _parse_item_specific(self, item_html: str, deal_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Soccer.com-specific data."""
        from selectolax.parser import HTMLParser
        parser = HTMLParser(item_html)
        
        # Extract SKU/Product ID
        sku_elem = parser.css_first('.product-sku, .sku, [data-sku]')
        if sku_elem:
            sku_text = clean_text(sku_elem.text())
            if sku_text:
                deal_data['sku'] = sku_text.replace('SKU:', '').strip()
        
        # Extract from data attributes
        item_elem = parser.css_first('[data-product-id], [data-sku], [data-item-id]')
        if item_elem:
            product_id = (item_elem.attributes.get('data-product-id') or 
                         item_elem.attributes.get('data-sku') or
                         item_elem.attributes.get('data-item-id'))
            if product_id:
                deal_data['sku'] = product_id
        
        # Extract brand
        brand_elem = parser.css_first('.brand-name, .product-brand, .manufacturer')
        if brand_elem:
            brand_text = clean_text(brand_elem.text())
            if brand_text:
                deal_data['brand'] = brand_text
        
        # Soccer.com is primarily soccer, but check category
        deal_data['sport'] = Sport.SOCCER.value
        
        # Extract category information
        category_elem = parser.css_first('.breadcrumb, .category-path, .product-category')
        if category_elem:
            category_text = category_elem.text()
            deal_data['category'] = self._map_category(category_text)
        
        # Extract size information
        size_container = parser.css_first('.size-selector, .size-options, .size-grid')
        if size_container:
            size_elements = size_container.css('a, button, .size-option')
            sizes = []
            for size_elem in size_elements:
                size_text = clean_text(size_elem.text())
                if size_text and size_text not in ['Select Size', 'Size', 'Choose Size']:
                    sizes.append(size_text)
            if sizes:
                deal_data['sizes'] = sizes
        
        # Extract stock status
        stock_elem = parser.css_first('.stock-status, .availability, .inventory')
        if stock_elem:
            stock_text = stock_elem.text().lower()
            if 'in stock' in stock_text or 'available' in stock_text:
                deal_data['in_stock'] = True
            elif 'out of stock' in stock_text or 'unavailable' in stock_text:
                deal_data['in_stock'] = False
            elif 'limited' in stock_text or 'low stock' in stock_text:
                deal_data['stock_level'] = 'limited'
        
        # Extract promotion information
        promo_elem = parser.css_first('.sale-badge, .clearance-badge, .promo-badge, .deal-tag')
        if promo_elem:
            promo_text = clean_text(promo_elem.text())
            if promo_text:
                deal_data['promotion_type'] = promo_text.lower()
        
        # Extract coupon information
        coupon_elem = parser.css_first('.coupon-code, .promo-code, .discount-code')
        if coupon_elem:
            coupon_text = clean_text(coupon_elem.text())
            coupon_code = extract_coupon_code(coupon_text)
            if coupon_code:
                deal_data['coupon_code'] = coupon_code
        
        # Enhanced youth detection for Soccer.com
        title = deal_data.get('title', '').lower()
        youth_indicators = [
            'youth', 'jr', 'junior', 'kids', 'boy', 'girl', 'child',
            'ys', 'ym', 'yl', 'yxl', 'yxxl',  # Youth sizes
            'little', 'small', 'toddler', 'infant'
        ]
        
        if any(indicator in title for indicator in youth_indicators):
            deal_data['youth_flag'] = True
        
        # Check for adult indicators
        adult_indicators = ['adult', 'men', 'mens', 'women', 'womens', 'man', 'woman']
        if any(indicator in title for indicator in adult_indicators):
            deal_data['youth_flag'] = False
        
        # Extract age range if available
        age_elem = parser.css_first('.age-range, .recommended-age, .age-group')
        if age_elem:
            age_text = clean_text(age_elem.text())
            if age_text:
                deal_data['age_range'] = age_text
        
        return deal_data
    
    def _map_category(self, category_text: str) -> str:
        """Map Soccer.com category text to our category enum."""
        category_text = category_text.lower()
        
        if any(word in category_text for word in ['shoe', 'cleat', 'sneaker', 'boot', 'footwear']):
            return Category.FOOTWEAR.value
        elif any(word in category_text for word in ['shirt', 'jersey', 'pant', 'short', 'jacket', 'apparel', 'clothing']):
            return Category.APPAREL.value
        elif any(word in category_text for word in ['helmet', 'pad', 'guard', 'protection', 'safety', 'shin']):
            return Category.PROTECTIVE.value
        elif any(word in category_text for word in ['ball', 'bat', 'stick', 'racket', 'club', 'equipment']):
            return Category.EQUIPMENT.value
        elif any(word in category_text for word in ['bag', 'backpack', 'duffel', 'luggage']):
            return Category.BAGS.value
        else:
            return Category.ACCESSORIES.value
    
    def _map_sport(self, category_text: str) -> str:
        """Map Soccer.com category text to our sport enum."""
        # Soccer.com is primarily soccer
        return Sport.SOCCER.value
    
    async def collect_deals(self) -> List[Deal]:
        """Collect deals from Soccer.com."""
        return await self.collect_deals_with_pagination()
