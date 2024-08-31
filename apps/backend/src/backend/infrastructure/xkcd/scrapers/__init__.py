from .base.base import BaseScraper
from .base.explain import XkcdExplainScraper
from .base.original import XkcdOriginalScraper
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
