"""Database utilities for storing and retrieving deals data."""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import dataset
from sqlalchemy import create_engine, text
from sqlmodel import SQLModel, create_engine as sqlmodel_create_engine

from .models import Deal, PriceHistory, ScrapingSession


class DatabaseManager:
    """Manages database operations for deals and related data."""
    
    def __init__(self, db_url: str = "sqlite:///data/deals.db"):
        """Initialize database manager."""
        self.db_url = db_url
        self.engine = None
        self.db = None
        self._setup_database()
    
    def _setup_database(self) -> None:
        """Set up database connection and tables."""
        # Create data directory if it doesn't exist
        if self.db_url.startswith("sqlite:///"):
            db_path = Path(self.db_url.replace("sqlite:///", ""))
            db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create SQLModel engine for schema management
        self.engine = sqlmodel_create_engine(self.db_url, echo=False)
        
        # Create tables
        SQLModel.metadata.create_all(self.engine)
        
        # Create dataset connection for easier operations
        self.db = dataset.connect(self.db_url)
    
    def save_deal(self, deal: Deal) -> bool:
        """Save a deal to the database."""
        try:
            deal_dict = deal.to_dict()
            
            # Use upsert to handle duplicates
            self.db['deals'].upsert(deal_dict, ['id'])
            return True
        except Exception as e:
            print(f"Error saving deal {deal.id}: {e}")
            return False
    
    def save_deals(self, deals: List[Deal]) -> int:
        """Save multiple deals to the database."""
        saved_count = 0
        for deal in deals:
            if self.save_deal(deal):
                saved_count += 1
        return saved_count
    
    def get_deal(self, deal_id: str) -> Optional[Deal]:
        """Get a deal by ID."""
        try:
            deal_data = self.db['deals'].find_one(id=deal_id)
            if deal_data:
                return self._dict_to_deal(deal_data)
            return None
        except Exception as e:
            print(f"Error getting deal {deal_id}: {e}")
            return None
    
    def get_deals(
        self,
        retailer: Optional[str] = None,
        sport: Optional[str] = None,
        min_discount: Optional[float] = None,
        youth_only: bool = False,
        limit: Optional[int] = None
    ) -> List[Deal]:
        """Get deals with optional filtering."""
        try:
            query = self.db['deals']
            
            # Apply filters
            if retailer:
                query = query.find(retailer=retailer)
            else:
                query = query.find()
            
            # Convert to list for further filtering
            deals_data = list(query)
            
            # Apply additional filters that can't be done in SQL
            filtered_deals = []
            for deal_data in deals_data:
                deal = self._dict_to_deal(deal_data)
                if deal is None:
                    continue
                
                # Sport filter
                if sport and deal.sport and deal.sport.value != sport:
                    continue
                
                # Discount filter
                if min_discount and (deal.discount_pct is None or deal.discount_pct < min_discount):
                    continue
                
                # Youth filter
                if youth_only and not deal.youth_flag:
                    continue
                
                filtered_deals.append(deal)
            
            # Apply limit
            if limit:
                filtered_deals = filtered_deals[:limit]
            
            return filtered_deals
        except Exception as e:
            print(f"Error getting deals: {e}")
            return []
    
    def get_recent_deals(self, hours: int = 24) -> List[Deal]:
        """Get deals found in the last N hours."""
        try:
            cutoff_time = datetime.utcnow().timestamp() - (hours * 3600)
            deals_data = self.db['deals'].find(last_seen={'>=': cutoff_time})
            return [self._dict_to_deal(deal_data) for deal_data in deals_data if self._dict_to_deal(deal_data)]
        except Exception as e:
            print(f"Error getting recent deals: {e}")
            return []
    
    def delete_old_deals(self, days: int = 30) -> int:
        """Delete deals older than N days."""
        try:
            cutoff_time = datetime.utcnow().timestamp() - (days * 24 * 3600)
            result = self.db['deals'].delete(last_seen={'<': cutoff_time})
            return result.rowcount if result else 0
        except Exception as e:
            print(f"Error deleting old deals: {e}")
            return 0
    
    def save_price_history(self, price_history: PriceHistory) -> bool:
        """Save price history entry."""
        try:
            history_dict = price_history.to_dict()
            self.db['price_history'].insert(history_dict)
            return True
        except Exception as e:
            print(f"Error saving price history: {e}")
            return False
    
    def get_price_history(self, deal_id: str, days: int = 30) -> List[PriceHistory]:
        """Get price history for a deal."""
        try:
            cutoff_time = datetime.utcnow().timestamp() - (days * 24 * 3600)
            history_data = self.db['price_history'].find(
                deal_id=deal_id,
                timestamp={'>=': cutoff_time}
            )
            return [self._dict_to_price_history(h) for h in history_data if self._dict_to_price_history(h)]
        except Exception as e:
            print(f"Error getting price history: {e}")
            return []
    
    def save_scraping_session(self, session: ScrapingSession) -> bool:
        """Save scraping session metadata."""
        try:
            session_dict = session.to_dict()
            self.db['scraping_sessions'].upsert(session_dict, ['session_id'])
            return True
        except Exception as e:
            print(f"Error saving scraping session: {e}")
            return False
    
    def get_scraping_sessions(self, retailer: Optional[str] = None, limit: int = 10) -> List[ScrapingSession]:
        """Get recent scraping sessions."""
        try:
            query = self.db['scraping_sessions']
            if retailer:
                sessions_data = query.find(retailer=retailer, _limit=limit, _order_by='-started_at')
            else:
                sessions_data = query.find(_limit=limit, _order_by='-started_at')
            return [self._dict_to_scraping_session(s) for s in sessions_data if self._dict_to_scraping_session(s)]
        except Exception as e:
            print(f"Error getting scraping sessions: {e}")
            return []
    
    def get_deal_count(self) -> int:
        """Get total number of deals in database."""
        try:
            return self.db['deals'].count()
        except Exception:
            return 0
    
    def get_retailer_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics by retailer."""
        try:
            stats = {}
            retailers = self.db['deals'].distinct('retailer')
            
            for retailer in retailers:
                retailer_deals = list(self.db['deals'].find(retailer=retailer))
                if not retailer_deals:
                    continue
                
                stats[retailer] = {
                    'total_deals': len(retailer_deals),
                    'youth_deals': len([d for d in retailer_deals if d.get('youth_flag')]),
                    'avg_discount': self._calculate_avg_discount(retailer_deals),
                    'last_updated': max(d.get('last_seen', 0) for d in retailer_deals)
                }
            
            return stats
        except Exception as e:
            print(f"Error getting retailer stats: {e}")
            return {}
    
    def _calculate_avg_discount(self, deals_data: List[Dict[str, Any]]) -> float:
        """Calculate average discount from deal data."""
        discounts = []
        for deal_data in deals_data:
            if deal_data.get('discount_pct') is not None:
                discounts.append(deal_data['discount_pct'])
        
        return sum(discounts) / len(discounts) if discounts else 0.0
    
    def _dict_to_deal(self, deal_data: Dict[str, Any]) -> Optional[Deal]:
        """Convert dictionary to Deal object."""
        try:
            # Convert timestamp fields back to datetime
            for field in ['last_seen', 'first_seen']:
                if field in deal_data and deal_data[field]:
                    if isinstance(deal_data[field], (int, float)):
                        deal_data[field] = datetime.fromtimestamp(deal_data[field])
                    elif isinstance(deal_data[field], str):
                        deal_data[field] = datetime.fromisoformat(deal_data[field].replace('Z', '+00:00'))
            
            # Convert URL fields back to HttpUrl
            for field in ['canonical_url', 'image_url', 'source_url']:
                if field in deal_data and deal_data[field]:
                    deal_data[field] = str(deal_data[field])
            
            # Convert Decimal fields
            for field in ['price', 'msrp']:
                if field in deal_data and deal_data[field] is not None:
                    deal_data[field] = str(deal_data[field])
            
            return Deal(**deal_data)
        except Exception as e:
            print(f"Error converting deal data: {e}")
            return None
    
    def _dict_to_price_history(self, history_data: Dict[str, Any]) -> Optional[PriceHistory]:
        """Convert dictionary to PriceHistory object."""
        try:
            # Convert timestamp
            if 'timestamp' in history_data and history_data['timestamp']:
                if isinstance(history_data['timestamp'], (int, float)):
                    history_data['timestamp'] = datetime.fromtimestamp(history_data['timestamp'])
                elif isinstance(history_data['timestamp'], str):
                    history_data['timestamp'] = datetime.fromisoformat(history_data['timestamp'].replace('Z', '+00:00'))
            
            # Convert Decimal fields
            for field in ['price', 'msrp']:
                if field in history_data and history_data[field] is not None:
                    history_data[field] = str(history_data[field])
            
            return PriceHistory(**history_data)
        except Exception as e:
            print(f"Error converting price history data: {e}")
            return None
    
    def _dict_to_scraping_session(self, session_data: Dict[str, Any]) -> Optional[ScrapingSession]:
        """Convert dictionary to ScrapingSession object."""
        try:
            # Convert timestamps
            for field in ['started_at', 'ended_at']:
                if field in session_data and session_data[field]:
                    if isinstance(session_data[field], (int, float)):
                        session_data[field] = datetime.fromtimestamp(session_data[field])
                    elif isinstance(session_data[field], str):
                        session_data[field] = datetime.fromisoformat(session_data[field].replace('Z', '+00:00'))
            
            return ScrapingSession(**session_data)
        except Exception as e:
            print(f"Error converting scraping session data: {e}")
            return None
    
    def close(self) -> None:
        """Close database connections."""
        if self.db:
            self.db.close()
        if self.engine:
            self.engine.dispose()


# Global database instance
_db_manager: Optional[DatabaseManager] = None


def get_database() -> DatabaseManager:
    """Get global database manager instance."""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager


def close_database() -> None:
    """Close global database connection."""
    global _db_manager
    if _db_manager:
        _db_manager.close()
        _db_manager = None
