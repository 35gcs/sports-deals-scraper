"""Deal deduplication system to identify and merge duplicate products."""

import hashlib
from typing import Dict, List, Optional, Set, Tuple

from fuzzywuzzy import fuzz
from fuzzywuzzy import process

from .models import Deal


class DealDeduplicator:
    """Identifies and merges duplicate deals across retailers."""
    
    def __init__(self, similarity_threshold: float = 0.85):
        """Initialize deduplicator with similarity threshold."""
        self.similarity_threshold = similarity_threshold
    
    def deduplicate_deals(self, deals: List[Deal]) -> List[Deal]:
        """Remove duplicates from deals list."""
        if not deals:
            return []
        
        # Group deals by potential duplicates
        duplicate_groups = self._group_duplicates(deals)
        
        # Merge each group into a single canonical deal
        canonical_deals = []
        for group in duplicate_groups:
            canonical_deal = self._merge_deal_group(group)
            canonical_deals.append(canonical_deal)
        
        return canonical_deals
    
    def _group_duplicates(self, deals: List[Deal]) -> List[List[Deal]]:
        """Group deals that are likely duplicates."""
        groups = []
        processed = set()
        
        for i, deal in enumerate(deals):
            if i in processed:
                continue
            
            # Start a new group with this deal
            group = [deal]
            processed.add(i)
            
            # Find similar deals
            for j, other_deal in enumerate(deals[i+1:], i+1):
                if j in processed:
                    continue
                
                if self._are_duplicates(deal, other_deal):
                    group.append(other_deal)
                    processed.add(j)
            
            groups.append(group)
        
        return groups
    
    def _are_duplicates(self, deal1: Deal, deal2: Deal) -> bool:
        """Check if two deals are duplicates."""
        # Check exact matches first
        if self._exact_match(deal1, deal2):
            return True
        
        # Check GTIN match
        if deal1.gtin and deal2.gtin and deal1.gtin == deal2.gtin:
            return True
        
        # Check MPN match
        if deal1.mpn and deal2.mpn and deal1.mpn == deal2.mpn:
            return True
        
        # Check SKU match (same retailer only)
        if (deal1.sku and deal2.sku and 
            deal1.sku == deal2.sku and 
            deal1.retailer == deal2.retailer):
            return True
        
        # Check fuzzy title match
        if self._fuzzy_title_match(deal1, deal2):
            return True
        
        return False
    
    def _exact_match(self, deal1: Deal, deal2: Deal) -> bool:
        """Check for exact matches on key fields."""
        # Same title, brand, and price (within 5%)
        if (deal1.title == deal2.title and 
            deal1.brand == deal2.brand and
            self._price_similar(deal1.price, deal2.price)):
            return True
        
        return False
    
    def _fuzzy_title_match(self, deal1: Deal, deal2: Deal) -> bool:
        """Check if titles are similar enough to be duplicates."""
        # Must have same brand
        if deal1.brand != deal2.brand:
            return False
        
        # Must have same sport
        if deal1.sport != deal2.sport:
            return False
        
        # Must have same category
        if deal1.category != deal2.category:
            return False
        
        # Check title similarity
        title_similarity = fuzz.ratio(deal1.title.lower(), deal2.title.lower())
        if title_similarity < self.similarity_threshold * 100:
            return False
        
        # Check if prices are similar (within 10%)
        if not self._price_similar(deal1.price, deal2.price, threshold=0.1):
            return False
        
        # Check if sizes overlap
        if not self._sizes_overlap(deal1.sizes, deal2.sizes):
            return False
        
        return True
    
    def _price_similar(self, price1: float, price2: float, threshold: float = 0.05) -> bool:
        """Check if two prices are similar within threshold."""
        if price1 == 0 or price2 == 0:
            return price1 == price2
        
        diff = abs(price1 - price2)
        avg_price = (price1 + price2) / 2
        return diff / avg_price <= threshold
    
    def _sizes_overlap(self, sizes1: Optional[List[str]], sizes2: Optional[List[str]]) -> bool:
        """Check if size lists overlap."""
        if not sizes1 or not sizes2:
            return True  # If one is missing, assume overlap
        
        # Normalize sizes
        sizes1_norm = {self._normalize_size(s) for s in sizes1}
        sizes2_norm = {self._normalize_size(s) for s in sizes2}
        
        # Check for overlap
        return bool(sizes1_norm & sizes2_norm)
    
    def _normalize_size(self, size: str) -> str:
        """Normalize size string for comparison."""
        return size.upper().strip()
    
    def _merge_deal_group(self, group: List[Deal]) -> Deal:
        """Merge a group of duplicate deals into a single canonical deal."""
        if len(group) == 1:
            return group[0]
        
        # Sort by score (highest first)
        group.sort(key=lambda d: d.score or 0, reverse=True)
        
        # Use the highest-scoring deal as the base
        canonical = group[0]
        
        # Collect alternate retailers
        alternate_retailers = []
        for deal in group[1:]:
            if deal.retailer != canonical.retailer:
                alternate_retailers.append(deal.retailer)
        
        if alternate_retailers:
            canonical.alternate_retailers = alternate_retailers
        
        # Mark other deals as duplicates
        for deal in group[1:]:
            deal.is_duplicate = True
            deal.canonical_deal_id = canonical.id
        
        # Update canonical deal with best information
        self._enhance_canonical_deal(canonical, group)
        
        return canonical
    
    def _enhance_canonical_deal(self, canonical: Deal, group: List[Deal]) -> None:
        """Enhance canonical deal with information from the group."""
        # Use the lowest price
        lowest_price = min(deal.price for deal in group)
        if lowest_price < canonical.price:
            canonical.price = lowest_price
        
        # Use the highest MSRP if available
        msrps = [deal.msrp for deal in group if deal.msrp]
        if msrps:
            canonical.msrp = max(msrps)
        
        # Combine sizes
        all_sizes = set()
        for deal in group:
            if deal.sizes:
                all_sizes.update(deal.sizes)
        
        if all_sizes:
            canonical.sizes = sorted(list(all_sizes))
        
        # Use the most recent last_seen
        canonical.last_seen = max(deal.last_seen for deal in group)
        
        # Use the earliest first_seen
        first_seens = [deal.first_seen for deal in group if deal.first_seen]
        if first_seens:
            canonical.first_seen = min(first_seens)
        
        # Combine coupon codes
        coupon_codes = [deal.coupon_code for deal in group if deal.coupon_code]
        if coupon_codes and not canonical.coupon_code:
            canonical.coupon_code = coupon_codes[0]
        
        # Use best stock status
        in_stock_deals = [deal for deal in group if deal.in_stock is True]
        if in_stock_deals:
            canonical.in_stock = True
        elif any(deal.in_stock is False for deal in group):
            canonical.in_stock = False
        
        # Use best stock level
        stock_levels = [deal.stock_level for deal in group if deal.stock_level]
        if stock_levels:
            # Prefer 'limited' over 'in stock'
            if 'limited' in stock_levels:
                canonical.stock_level = 'limited'
            else:
                canonical.stock_level = stock_levels[0]
        
        # Combine shipping notes
        shipping_notes = [deal.shipping_notes for deal in group if deal.shipping_notes]
        if shipping_notes and not canonical.shipping_notes:
            canonical.shipping_notes = shipping_notes[0]
    
    def find_duplicates(self, deals: List[Deal]) -> List[Tuple[Deal, Deal]]:
        """Find pairs of duplicate deals."""
        duplicates = []
        
        for i, deal1 in enumerate(deals):
            for deal2 in deals[i+1:]:
                if self._are_duplicates(deal1, deal2):
                    duplicates.append((deal1, deal2))
        
        return duplicates
    
    def get_duplicate_groups(self, deals: List[Deal]) -> List[List[Deal]]:
        """Get groups of duplicate deals."""
        return self._group_duplicates(deals)
    
    def get_canonical_deals(self, deals: List[Deal]) -> List[Deal]:
        """Get canonical deals (one per duplicate group)."""
        groups = self._group_duplicates(deals)
        return [self._merge_deal_group(group) for group in groups]
    
    def get_duplicate_count(self, deals: List[Deal]) -> int:
        """Get number of duplicate deals found."""
        groups = self._group_duplicates(deals)
        total_duplicates = sum(len(group) - 1 for group in groups if len(group) > 1)
        return total_duplicates
    
    def get_deduplication_stats(self, deals: List[Deal]) -> Dict[str, any]:
        """Get deduplication statistics."""
        groups = self._group_duplicates(deals)
        
        total_deals = len(deals)
        canonical_deals = len(groups)
        duplicate_groups = len([g for g in groups if len(g) > 1])
        total_duplicates = sum(len(group) - 1 for group in groups if len(group) > 1)
        
        return {
            'total_deals': total_deals,
            'canonical_deals': canonical_deals,
            'duplicate_groups': duplicate_groups,
            'total_duplicates': total_duplicates,
            'deduplication_rate': round((total_duplicates / total_deals) * 100, 1) if total_deals > 0 else 0,
        }
    
    def get_retailer_overlap(self, deals: List[Deal]) -> Dict[str, List[str]]:
        """Get which retailers have overlapping products."""
        groups = self._group_duplicates(deals)
        
        retailer_overlap = {}
        for group in groups:
            if len(group) > 1:
                retailers = [deal.retailer for deal in group]
                for retailer in retailers:
                    if retailer not in retailer_overlap:
                        retailer_overlap[retailer] = []
                    for other_retailer in retailers:
                        if other_retailer != retailer and other_retailer not in retailer_overlap[retailer]:
                            retailer_overlap[retailer].append(other_retailer)
        
        return retailer_overlap
    
    def get_brand_overlap(self, deals: List[Deal]) -> Dict[str, List[str]]:
        """Get which brands have overlapping products across retailers."""
        groups = self._group_duplicates(deals)
        
        brand_overlap = {}
        for group in groups:
            if len(group) > 1:
                brands = [deal.brand for deal in group if deal.brand]
                if len(brands) > 1:
                    for brand in brands:
                        if brand not in brand_overlap:
                            brand_overlap[brand] = []
                        for other_brand in brands:
                            if other_brand != brand and other_brand not in brand_overlap[brand]:
                                brand_overlap[brand].append(other_brand)
        
        return brand_overlap
