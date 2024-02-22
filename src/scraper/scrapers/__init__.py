from .origin import XkcdOriginScraper
from .translation_scrapers.CN import XkcdCNScraper
from .translation_scrapers.DE import XkcdDEScraper
from .translation_scrapers.ES import XkcdESScraper
from .translation_scrapers.FR import XkcdFRScraper
from .translation_scrapers.RU import XkcdRUScraper

__all__ = [
    "XkcdOriginScraper",
    "XkcdCNScraper",
    "XkcdDEScraper",
    "XkcdESScraper",
    "XkcdFRScraper",
    "XkcdRUScraper",
]
