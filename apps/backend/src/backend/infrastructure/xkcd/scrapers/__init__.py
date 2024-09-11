from .base import BaseScraper
from .explain import XkcdExplainScraper
from .original import XkcdOriginalScraper
from .translations.DE import XkcdDEScraper
from .translations.ES import XkcdESScraper
from .translations.FR import XkcdFRScraper
from .translations.RU import XkcdRUScraper
from .translations.ZH import XkcdZHScraper

__all__ = [
    "BaseScraper",
    "XkcdOriginalScraper",
    "XkcdExplainScraper",
    "XkcdDEScraper",
    "XkcdESScraper",
    "XkcdFRScraper",
    "XkcdRUScraper",
    "XkcdZHScraper",
]
