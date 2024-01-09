from dataclasses import dataclass
from datetime import datetime as dt

from src.core.types import Language

from .models import ComicModel
from .translations.dtos import TranslationGetDTO


@dataclass(slots=True)
class ComicBaseCreateDTO:
    issue_number: int | None
    publication_date: dt.date
    xkcd_url: str | None
    explain_url: str | None
    reddit_url: str | None
    link_on_click: str | None
    is_interactive: bool
    tags: list[str]


@dataclass(slots=True)
class ComicGetDTO:
    id: int
    issue_number: int | None
    publication_date: dt.date
    xkcd_url: str | None
    explain_url: str | None
    reddit_url: str | None
    link_on_click: str | None
    is_interactive: bool
    tags: list[str]
    translations: dict[Language, TranslationGetDTO]

    @classmethod
    def from_model(cls, model: ComicModel) -> "ComicGetDTO":
        translations = {}
        for tr in model.translations:
            translations = translations | TranslationGetDTO.from_model(tr)

        return ComicGetDTO(
            id=model.id,
            issue_number=model.issue_number,
            publication_date=model.publication_date,
            xkcd_url=model.xkcd_url,
            explain_url=model.explain_url,
            reddit_url=model.reddit_url,
            link_on_click=model.link_on_click,
            is_interactive=model.is_interactive,
            tags=[tag.name for tag in model.tags],
            translations=translations,
        )
