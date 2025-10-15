"""Scoring utilities for ranking deals by quality and relevance."""

from decimal import Decimal
from typing import Dict, List, Optional

from ..models import Deal, Sport


# Brand prestige scores (0-10 scale)
BRAND_SCORES: Dict[str, float] = {
    # Premium brands
    'NIKE': 8.5,
    'ADIDAS': 8.0,
    'UNDER ARMOUR': 7.5,
    'PUMA': 7.0,
    'NEW BALANCE': 7.0,
    'ASICS': 6.5,
    'MIZUNO': 6.5,
    'WILSON': 6.5,
    'HEAD': 6.5,
    'BABOLAT': 6.5,
    
    # Specialist sports brands
    'BAUER': 8.0,  # Hockey
    'CCM': 7.5,    # Hockey
    'WARRIOR': 7.0, # Hockey
    'SHER-WOOD': 6.5, # Hockey
    'EASTON': 7.0,  # Baseball/Hockey
    'RAWLINGS': 7.0, # Baseball
    'WILSON': 6.5,  # Baseball
    'LOUISVILLE': 6.5, # Baseball
    'MOLTEN': 6.0,  # Basketball
    'SPALDING': 6.0, # Basketball
    
    # Soccer brands
    'ADIDAS': 8.0,
    'NIKE': 8.5,
    'PUMA': 7.0,
    'UMBRO': 6.5,
    'KAPPA': 6.0,
    'DIADORA': 6.0,
    
    # Running brands
    'BROOKS': 7.5,
    'SAUCONY': 7.0,
    'HOKA': 7.5,
    'ON': 7.0,
    'ALTRA': 6.5,
    
    # Value brands
    'CHAMPION': 5.0,
    'RUSSELL': 4.5,
    'STARTER': 4.0,
    'FRUIT OF THE LOOM': 3.5,
}

# Sport-specific brand bonuses
SPORT_BRAND_BONUSES: Dict[Sport, Dict[str, float]] = {
    Sport.HOCKEY: {
        'BAUER': 2.0,
        'CCM': 1.5,
        'WARRIOR': 1.0,
        'SHER-WOOD': 0.5,
    },
    Sport.BASEBALL: {
        'EASTON': 1.5,
        'RAWLINGS': 1.5,
        'WILSON': 1.0,
        'LOUISVILLE': 1.0,
    },
    Sport.SOCCER: {
        'ADIDAS': 1.0,
        'NIKE': 1.0,
        'PUMA': 0.5,
        'UMBRO': 0.5,
    },
    Sport.TENNIS: {
        'WILSON': 1.5,
        'HEAD': 1.5,
        'BABOLAT': 1.5,
        'YONEX': 1.0,
    },
    Sport.RUNNING: {
        'BROOKS': 1.5,
        'SAUCONY': 1.0,
        'HOKA': 1.5,
        'ASICS': 1.0,
    },
}


def calculate_discount_score(deal: Deal) -> float:
    """Calculate discount-based score (0-45 points)."""
    if not deal.discount_pct:
        return 0.0
    
    # Cap at 45 points, with diminishing returns for very high discounts
    discount_pct = min(deal.discount_pct, 90)  # Cap at 90% to avoid fake MSRPs
    
    # Use logarithmic scaling for diminishing returns
    import math
    score = min(45, discount_pct * 0.9)

    # Bonus for very high discounts (70%+), still respecting the cap
    if discount_pct >= 70:
        score = min(45, score + 5)

    return round(score, 1)


def calculate_price_score(deal: Deal) -> float:
    """Calculate price-based score (0-20 points)."""
    price = float(deal.price)
    
    # Lower prices get higher scores (inverted scale)
    # Typical youth sports gear price ranges:
    # $5-20: Excellent (20 points)
    # $20-40: Good (15 points) 
    # $40-60: Fair (10 points)
    # $60-100: Poor (5 points)
    # $100+: Very poor (0 points)
    
    if price <= 20:
        return 20.0
    elif price <= 40:
        return 20.0 - ((price - 20) * 0.25)  # Linear decrease
    elif price <= 60:
        return 15.0 - ((price - 40) * 0.25)
    elif price <= 100:
        return 10.0 - ((price - 60) * 0.125)
    else:
        return max(0.0, 5.0 - ((price - 100) * 0.05))


def calculate_youth_score(deal: Deal) -> float:
    """Calculate youth relevance score (0-20 points)."""
    score = 0.0
    
    # Strong youth indicators
    if deal.youth_flag:
        score += 15.0
    
    # Size-based scoring
    if deal.sizes:
        youth_sizes = 0
        total_sizes = len(deal.sizes)
        
        for size in deal.sizes:
            size_upper = size.upper()
            if any(keyword in size_upper for keyword in ['Y', 'JR', 'JUNIOR', 'KIDS', 'BOY', 'GIRL']):
                youth_sizes += 1
        
        if youth_sizes > 0:
            youth_ratio = youth_sizes / total_sizes
            score += youth_ratio * 5.0
    
    # Title/keyword analysis
    title_lower = deal.title.lower()
    youth_keywords = ['youth', 'jr', 'junior', 'kids', 'boy', 'girl', 'child']
    adult_keywords = ['adult', 'men', 'mens', 'women', 'womens']
    
    if any(keyword in title_lower for keyword in youth_keywords):
        score += 3.0
    
    if any(keyword in title_lower for keyword in adult_keywords):
        score -= 5.0  # Strong negative signal
    
    # Age range bonus
    if deal.age_range:
        score += 2.0
    
    return min(20.0, max(0.0, score))


def calculate_brand_score(deal: Deal) -> float:
    """Calculate brand prestige score (0-10 points)."""
    if not deal.brand:
        return 0.0
    
    brand_upper = deal.brand.upper().strip()
    base_score = BRAND_SCORES.get(brand_upper, 5.0)  # Default to middle score
    
    # Add sport-specific bonus
    if deal.sport and deal.sport in SPORT_BRAND_BONUSES:
        sport_bonus = SPORT_BRAND_BONUSES[deal.sport].get(brand_upper, 0.0)
        base_score += sport_bonus
    
    return min(10.0, base_score)


def calculate_inventory_score(deal: Deal) -> float:
    """Calculate inventory/supply score (0-5 points)."""
    score = 0.0
    
    # Stock status
    if deal.in_stock is True:
        score += 2.0
    elif deal.in_stock is False:
        score -= 2.0
    
    # Stock level indicators
    if deal.stock_level:
        stock_lower = deal.stock_level.lower()
        if 'limited' in stock_lower or 'low' in stock_lower:
            score += 1.0  # Urgency bonus
        elif 'in stock' in stock_lower or 'available' in stock_lower:
            score += 0.5
    
    # Size availability
    if deal.sizes and len(deal.sizes) >= 3:
        score += 1.0  # Good size selection
    
    # Coupon availability
    if deal.coupon_code:
        score += 1.0

    # Reward deals that have strong availability signals across the board
    if (
        deal.in_stock is True
        and deal.sizes and len(deal.sizes) >= 3
        and deal.coupon_code
    ):
        score += 1.0
    
    return min(5.0, max(0.0, score))


def calculate_composite_score(deal: Deal) -> float:
    """Calculate overall composite score (0-100 points)."""
    discount_score = calculate_discount_score(deal)
    price_score = calculate_price_score(deal)
    youth_score = calculate_youth_score(deal)
    brand_score = calculate_brand_score(deal)
    inventory_score = calculate_inventory_score(deal)
    
    total_score = (
        discount_score +      # 0-45 points
        price_score +         # 0-20 points
        youth_score +         # 0-20 points
        brand_score +         # 0-10 points
        inventory_score       # 0-5 points
    )
    
    return round(min(100.0, total_score), 1)


def calculate_relevance_score(deal: Deal, target_sport: Optional[Sport] = None) -> float:
    """Calculate relevance score for specific sport or general youth sports."""
    score = 0.0
    
    # Sport relevance
    if target_sport and deal.sport == target_sport:
        score += 30.0
    elif deal.sport:
        score += 15.0  # General sports relevance
    
    # Youth relevance
    youth_score = calculate_youth_score(deal)
    score += youth_score * 0.5  # Weight youth score
    
    # Category relevance
    if deal.category:
        score += 10.0
    
    # Brand relevance
    brand_score = calculate_brand_score(deal)
    score += brand_score * 0.3  # Weight brand score
    
    return min(100.0, score)


def rank_deals(deals: List[Deal], min_discount: float = 0.0) -> List[Deal]:
    """Rank deals by composite score and filter by minimum discount."""
    # Calculate scores for all deals
    for deal in deals:
        deal.score = calculate_composite_score(deal)
        deal.relevance_score = calculate_relevance_score(deal)
    
    # Filter by minimum discount
    filtered_deals = [
        deal for deal in deals 
        if deal.discount_pct is None or deal.discount_pct >= min_discount
    ]
    
    # Sort by composite score (descending)
    ranked_deals = sorted(filtered_deals, key=lambda d: d.score or 0, reverse=True)
    
    return ranked_deals


def get_top_deals_by_sport(deals: List[Deal], top_per_sport: int = 8) -> Dict[Sport, List[Deal]]:
    """Get top deals grouped by sport."""
    sport_deals: Dict[Sport, List[Deal]] = {}
    
    # Group deals by sport
    for deal in deals:
        if deal.sport:
            if deal.sport not in sport_deals:
                sport_deals[deal.sport] = []
            sport_deals[deal.sport].append(deal)
    
    # Sort each sport's deals and take top N
    for sport in sport_deals:
        sport_deals[sport] = sorted(
            sport_deals[sport], 
            key=lambda d: d.score or 0, 
            reverse=True
        )[:top_per_sport]
    
    return sport_deals


def get_top_deals_by_category(deals: List[Deal], top_per_category: int = 5) -> Dict[str, List[Deal]]:
    """Get top deals grouped by category."""
    category_deals: Dict[str, List[Deal]] = {}
    
    # Group deals by category
    for deal in deals:
        category = deal.category.value if deal.category else "other"
        if category not in category_deals:
            category_deals[category] = []
        category_deals[category].append(deal)
    
    # Sort each category's deals and take top N
    for category in category_deals:
        category_deals[category] = sorted(
            category_deals[category],
            key=lambda d: d.score or 0,
            reverse=True
        )[:top_per_category]
    
    return category_deals
