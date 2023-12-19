from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import datetime as dt

from .translations.dtos import TranslationCreateDTO


@dataclass(slots=True)
class ComicCreateDTO:
    issue_number: int | None
    publication_date: dt.date
    xkcd_url: str | None
    explain_url: str | None
    reddit_url: str | None
    link_on_click: str | None
    is_interactive: bool
    is_extra: bool
    tags: list[str]
    translation: TranslationCreateDTO

    def to_dict(self, exclude=Iterable[str]):
        d = asdict(self)
        for ex in exclude:
            d.pop(ex)
        return d
