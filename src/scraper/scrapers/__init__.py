from .explain import XkcdExplainScraper
from .origin import XkcdOriginScraper
from .origin_with_explain_data import XkcdOriginWithExplainDataScraper
from .translation_scrapers.CN import XkcdCNScraper
from .translation_scrapers.DE import XkcdDEScraper
from .translation_scrapers.ES import XkcdESScraper
from .translation_scrapers.FR import XkcdFRScraper
from .translation_scrapers.RU import XkcdRUScraper

__all__ = [
    "XkcdOriginScraper",
    "XkcdExplainScraper",
    "XkcdOriginWithExplainDataScraper",
    "XkcdCNScraper",
    "XkcdDEScraper",
    "XkcdESScraper",
    "XkcdFRScraper",
    "XkcdRUScraper",
]
