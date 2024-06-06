import logging

from slugify import slugify as base_slugify

logger = logging.getLogger(__name__)


def slugify(words: str) -> str:
    slug = base_slugify(
        words,
        separator="-",
        replacements=(
            ("+", " plus "),
            ("%", " percent "),
            ("(", " lr_br "),
            (")", " rr_br "),
            ("[", " ls_br "),
            ("]", " rs_br "),
            ("{", " lc_br "),
            ("}", " rc_br "),
        ),
    )
    if not slug:
        logger.error("Can't slugify words: %s", words)
        return words
    return slug
