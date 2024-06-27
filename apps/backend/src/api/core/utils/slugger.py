import logging

from slugify import slugify as base_slugify

logger = logging.getLogger(__name__)


def slugify(
    string: str,
    separator: str = "-",
    replacements: tuple[tuple[str, str]] = (
        ("+", " plus "),
        ("%", " pct "),
    ),
) -> str:
    slug = base_slugify(string, separator=separator, replacements=replacements)
    if not slug:
        logger.error("Can't slugify words: %s", string)
        return string
    return slug
