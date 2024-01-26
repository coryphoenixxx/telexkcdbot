from slugify import slugify as base_slugify

from api.core.exceptions import CreatedEmptySlugError


def slugify(word: str) -> str:
    slug = base_slugify(
        word,
        separator="_",
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
        raise CreatedEmptySlugError(word=word)
    return slug
