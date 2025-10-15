"""Deal ranking and scoring system."""

from typing import Dict, List, Optional

from .models import Deal, Sport
from .utils.scoring import (
    calculate_composite_score,
    calculate_relevance_score,
    rank_deals,
    get_top_deals_by_sport,
    get_top_deals_by_category,
)


class DealRanker:
    """Ranks and scores deals based on multiple criteria."""
    
    def __init__(self, min_discount: float = 0.0):
        """Initialize ranker with minimum discount threshold."""
        self.min_discount = min_discount
    
    def rank_deals(self, deals: List[Deal]) -> List[Deal]:
        """Rank deals by composite score."""
        return rank_deals(deals, self.min_discount)
    
    def score_deals(self, deals: List[Deal]) -> List[Deal]:
        """Calculate scores for all deals."""
        for deal in deals:
            deal.score = calculate_composite_score(deal)
            deal.relevance_score = calculate_relevance_score(deal)
        return deals
    
    def get_top_deals(self, deals: List[Deal], limit: int = 50) -> List[Deal]:
        """Get top N deals by score."""
        scored_deals = self.score_deals(deals)
        ranked_deals = self.rank_deals(scored_deals)
        return ranked_deals[:limit]
    
    def get_top_deals_by_sport(self, deals: List[Deal], top_per_sport: int = 8) -> Dict[Sport, List[Deal]]:
        """Get top deals grouped by sport."""
        scored_deals = self.score_deals(deals)
        return get_top_deals_by_sport(scored_deals, top_per_sport)
    
    def get_top_deals_by_category(self, deals: List[Deal], top_per_category: int = 5) -> Dict[str, List[Deal]]:
        """Get top deals grouped by category."""
        scored_deals = self.score_deals(deals)
        return get_top_deals_by_category(scored_deals, top_per_category)
    
    def get_youth_deals(self, deals: List[Deal], limit: Optional[int] = None) -> List[Deal]:
        """Get top youth deals."""
        youth_deals = [deal for deal in deals if deal.youth_flag]
        scored_deals = self.score_deals(youth_deals)
        ranked_deals = self.rank_deals(scored_deals)
        return ranked_deals[:limit] if limit else ranked_deals
    
    def get_deals_by_sport(self, deals: List[Deal], sport: Sport, limit: Optional[int] = None) -> List[Deal]:
        """Get top deals for specific sport."""
        sport_deals = [deal for deal in deals if deal.sport == sport]
        scored_deals = self.score_deals(sport_deals)
        ranked_deals = self.rank_deals(scored_deals)
        return ranked_deals[:limit] if limit else ranked_deals
    
    def get_deals_by_category(self, deals: List[Deal], category: str, limit: Optional[int] = None) -> List[Deal]:
        """Get top deals for specific category."""
        category_deals = [deal for deal in deals if deal.category and deal.category.value == category]
        scored_deals = self.score_deals(category_deals)
        ranked_deals = self.rank_deals(scored_deals)
        return ranked_deals[:limit] if limit else ranked_deals
    
    def get_best_discounts(self, deals: List[Deal], limit: int = 20) -> List[Deal]:
        """Get deals with highest discount percentages."""
        deals_with_discount = [deal for deal in deals if deal.discount_pct is not None]
        sorted_deals = sorted(deals_with_discount, key=lambda d: d.discount_pct or 0, reverse=True)
        return sorted_deals[:limit]
    
    def get_lowest_prices(self, deals: List[Deal], limit: int = 20) -> List[Deal]:
        """Get deals with lowest absolute prices."""
        sorted_deals = sorted(deals, key=lambda d: float(d.price))
        return sorted_deals[:limit]
    
    def get_brand_deals(self, deals: List[Deal], brand: str, limit: Optional[int] = None) -> List[Deal]:
        """Get top deals for specific brand."""
        brand_deals = [deal for deal in deals if deal.brand and deal.brand.lower() == brand.lower()]
        scored_deals = self.score_deals(brand_deals)
        ranked_deals = self.rank_deals(scored_deals)
        return ranked_deals[:limit] if limit else ranked_deals
    
    def get_retailer_deals(self, deals: List[Deal], retailer: str, limit: Optional[int] = None) -> List[Deal]:
        """Get top deals from specific retailer."""
        retailer_deals = [deal for deal in deals if deal.retailer.lower() == retailer.lower()]
        scored_deals = self.score_deals(retailer_deals)
        ranked_deals = self.rank_deals(retailer_deals)
        return ranked_deals[:limit] if limit else ranked_deals
    
    def get_deals_with_coupons(self, deals: List[Deal], limit: Optional[int] = None) -> List[Deal]:
        """Get deals that have coupon codes."""
        coupon_deals = [deal for deal in deals if deal.coupon_code]
        scored_deals = self.score_deals(coupon_deals)
        ranked_deals = self.rank_deals(scored_deals)
        return ranked_deals[:limit] if limit else ranked_deals
    
    def get_in_stock_deals(self, deals: List[Deal], limit: Optional[int] = None) -> List[Deal]:
        """Get deals that are in stock."""
        in_stock_deals = [deal for deal in deals if deal.in_stock is True]
        scored_deals = self.score_deals(in_stock_deals)
        ranked_deals = self.rank_deals(scored_deals)
        return ranked_deals[:limit] if limit else ranked_deals
    
    def get_limited_stock_deals(self, deals: List[Deal], limit: Optional[int] = None) -> List[Deal]:
        """Get deals with limited stock (urgency)."""
        limited_deals = [deal for deal in deals if deal.stock_level == 'limited']
        scored_deals = self.score_deals(limited_deals)
        ranked_deals = self.rank_deals(scored_deals)
        return ranked_deals[:limit] if limit else ranked_deals
    
    def get_deals_by_price_range(self, deals: List[Deal], min_price: float, max_price: float, limit: Optional[int] = None) -> List[Deal]:
        """Get deals within specific price range."""
        price_range_deals = [
            deal for deal in deals 
            if min_price <= float(deal.price) <= max_price
        ]
        scored_deals = self.score_deals(price_range_deals)
        ranked_deals = self.rank_deals(scored_deals)
        return ranked_deals[:limit] if limit else ranked_deals
    
    def get_deals_by_discount_range(self, deals: List[Deal], min_discount: float, max_discount: float, limit: Optional[int] = None) -> List[Deal]:
        """Get deals within specific discount range."""
        discount_range_deals = [
            deal for deal in deals 
            if deal.discount_pct is not None and min_discount <= deal.discount_pct <= max_discount
        ]
        scored_deals = self.score_deals(discount_range_deals)
        ranked_deals = self.rank_deals(scored_deals)
        return ranked_deals[:limit] if limit else ranked_deals
    
    def get_deals_by_size(self, deals: List[Deal], size: str, limit: Optional[int] = None) -> List[Deal]:
        """Get deals available in specific size."""
        size_deals = [
            deal for deal in deals 
            if deal.sizes and size.upper() in [s.upper() for s in deal.sizes]
        ]
        scored_deals = self.score_deals(size_deals)
        ranked_deals = self.rank_deals(scored_deals)
        return ranked_deals[:limit] if limit else ranked_deals
    
    def get_deals_by_age_range(self, deals: List[Deal], age_range: str, limit: Optional[int] = None) -> List[Deal]:
        """Get deals for specific age range."""
        age_deals = [
            deal for deal in deals 
            if deal.age_range and age_range.lower() in deal.age_range.lower()
        ]
        scored_deals = self.score_deals(age_deals)
        ranked_deals = self.rank_deals(scored_deals)
        return ranked_deals[:limit] if limit else ranked_deals
    
    def get_deals_ending_soon(self, deals: List[Deal], limit: Optional[int] = None) -> List[Deal]:
        """Get deals that are ending soon."""
        from datetime import datetime, timedelta
        
        ending_soon_deals = []
        for deal in deals:
            if deal.ends_at:
                # Deals ending within 7 days
                if deal.ends_at <= datetime.utcnow() + timedelta(days=7):
                    ending_soon_deals.append(deal)
        
        scored_deals = self.score_deals(ending_soon_deals)
        ranked_deals = self.rank_deals(scored_deals)
        return ranked_deals[:limit] if limit else ranked_deals
    
    def get_deals_by_retailer(self, deals: List[Deal], retailers: List[str], limit: Optional[int] = None) -> List[Deal]:
        """Get deals from specific retailers."""
        retailer_deals = [
            deal for deal in deals 
            if deal.retailer.lower() in [r.lower() for r in retailers]
        ]
        scored_deals = self.score_deals(retailer_deals)
        ranked_deals = self.rank_deals(scored_deals)
        return ranked_deals[:limit] if limit else ranked_deals
    
    def get_deals_by_brands(self, deals: List[Deal], brands: List[str], limit: Optional[int] = None) -> List[Deal]:
        """Get deals from specific brands."""
        brand_deals = [
            deal for deal in deals 
            if deal.brand and deal.brand.lower() in [b.lower() for b in brands]
        ]
        scored_deals = self.score_deals(brand_deals)
        ranked_deals = self.rank_deals(scored_deals)
        return ranked_deals[:limit] if limit else ranked_deals
    
    def get_deals_by_sports(self, deals: List[Deal], sports: List[Sport], limit: Optional[int] = None) -> List[Deal]:
        """Get deals for specific sports."""
        sport_deals = [
            deal for deal in deals 
            if deal.sport and deal.sport in sports
        ]
        scored_deals = self.score_deals(sport_deals)
        ranked_deals = self.rank_deals(scored_deals)
        return ranked_deals[:limit] if limit else ranked_deals
    
    def get_deals_by_categories(self, deals: List[Deal], categories: List[str], limit: Optional[int] = None) -> List[Deal]:
        """Get deals for specific categories."""
        category_deals = [
            deal for deal in deals 
            if deal.category and deal.category.value in categories
        ]
        scored_deals = self.score_deals(category_deals)
        ranked_deals = self.rank_deals(scored_deals)
        return ranked_deals[:limit] if limit else ranked_deals
    
    def get_deals_by_multiple_criteria(
        self, 
        deals: List[Deal], 
        sport: Optional[Sport] = None,
        category: Optional[str] = None,
        brand: Optional[str] = None,
        retailer: Optional[str] = None,
        youth_only: bool = False,
        in_stock_only: bool = False,
        min_discount: Optional[float] = None,
        max_price: Optional[float] = None,
        limit: Optional[int] = None
    ) -> List[Deal]:
        """Get deals matching multiple criteria."""
        filtered_deals = deals
        
        if sport:
            filtered_deals = [deal for deal in filtered_deals if deal.sport == sport]
        
        if category:
            filtered_deals = [deal for deal in filtered_deals if deal.category and deal.category.value == category]
        
        if brand:
            filtered_deals = [deal for deal in filtered_deals if deal.brand and deal.brand.lower() == brand.lower()]
        
        if retailer:
            filtered_deals = [deal for deal in filtered_deals if deal.retailer.lower() == retailer.lower()]
        
        if youth_only:
            filtered_deals = [deal for deal in filtered_deals if deal.youth_flag]
        
        if in_stock_only:
            filtered_deals = [deal for deal in filtered_deals if deal.in_stock is True]
        
        if min_discount is not None:
            filtered_deals = [deal for deal in filtered_deals if deal.discount_pct is not None and deal.discount_pct >= min_discount]
        
        if max_price is not None:
            filtered_deals = [deal for deal in filtered_deals if float(deal.price) <= max_price]
        
        scored_deals = self.score_deals(filtered_deals)
        ranked_deals = self.rank_deals(scored_deals)
        return ranked_deals[:limit] if limit else ranked_deals
    
    def get_deals_summary(self, deals: List[Deal]) -> Dict[str, any]:
        """Get summary statistics for deals."""
        if not deals:
            return {}
        
        total_deals = len(deals)
        youth_deals = len([deal for deal in deals if deal.youth_flag])
        in_stock_deals = len([deal for deal in deals if deal.in_stock is True])
        coupon_deals = len([deal for deal in deals if deal.coupon_code])
        
        # Calculate average discount
        deals_with_discount = [deal for deal in deals if deal.discount_pct is not None]
        avg_discount = sum(deal.discount_pct for deal in deals_with_discount) / len(deals_with_discount) if deals_with_discount else 0
        
        # Calculate average price
        avg_price = sum(float(deal.price) for deal in deals) / total_deals
        
        # Get top sports
        sport_counts = {}
        for deal in deals:
            if deal.sport:
                sport_counts[deal.sport.value] = sport_counts.get(deal.sport.value, 0) + 1
        
        # Get top brands
        brand_counts = {}
        for deal in deals:
            if deal.brand:
                brand_counts[deal.brand] = brand_counts.get(deal.brand, 0) + 1
        
        # Get top retailers
        retailer_counts = {}
        for deal in deals:
            retailer_counts[deal.retailer] = retailer_counts.get(deal.retailer, 0) + 1
        
        return {
            'total_deals': total_deals,
            'youth_deals': youth_deals,
            'in_stock_deals': in_stock_deals,
            'coupon_deals': coupon_deals,
            'avg_discount': round(avg_discount, 1),
            'avg_price': round(avg_price, 2),
            'top_sports': sorted(sport_counts.items(), key=lambda x: x[1], reverse=True)[:5],
            'top_brands': sorted(brand_counts.items(), key=lambda x: x[1], reverse=True)[:5],
            'top_retailers': sorted(retailer_counts.items(), key=lambda x: x[1], reverse=True)[:5],
        }
