from .base.base import BaseScraper
from .base.explain import XkcdExplainScraper
from .base.origin import XkcdOriginScraper
from .translations.DE import XkcdDEScraper
from .translations.ES import XkcdESScraper
from .translations.FR import XkcdFRScraper
from .translations.RU import XkcdRUScraper
from .translations.ZH import XkcdZHScraper

__all__ = [
    "BaseScraper",
    "XkcdOriginScraper",
    "XkcdExplainScraper",
    "XkcdDEScraper",
    "XkcdESScraper",
    "XkcdFRScraper",
    "XkcdRUScraper",
    "XkcdZHScraper",
]
