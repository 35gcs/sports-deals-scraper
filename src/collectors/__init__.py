"""Collectors package for scraping deals from various retailers."""

from .base import BaseCollector, CollectorError
from .dicks import DicksCollector
from .academy import AcademyCollector
from .scheels import ScheelsCollector
from .big5 import Big5Collector
from .nike import NikeCollector
from .adidas import AdidasCollector
from .soccer_com import SoccerComCollector
from .monkey_sports import MonkeySportsCollector

__all__ = [
    "BaseCollector",
    "CollectorError", 
    "DicksCollector",
    "AcademyCollector",
    "ScheelsCollector",
    "Big5Collector",
    "NikeCollector",
    "AdidasCollector",
    "SoccerComCollector",
    "MonkeySportsCollector",
]
