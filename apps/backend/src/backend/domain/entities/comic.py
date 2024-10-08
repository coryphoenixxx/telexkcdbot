import datetime as dt
from dataclasses import dataclass

from backend.domain.utils import build_searchable_text
from backend.domain.value_objects import ComicId, IssueNumber, TranslationId, TranslationTitle


@dataclass(slots=True, kw_only=True)
class ComicEntity:
    id: ComicId
    number: IssueNumber | None
    title: TranslationTitle
    tooltip: str
    publication_date: dt.date
    xkcd_url: str | None
    explain_url: str | None
    click_url: str | None
    is_interactive: bool
    original_translation_id: TranslationId
    transcript: str

    def set_title(self, title: str) -> None:
        self.title = TranslationTitle(title)

    @property
    def slug(self) -> str | None:
        return self.title.slug if self.number is None else None

    @property
    def searchable_text(self) -> str:
        return build_searchable_text(self.title.value, self.transcript)


@dataclass(slots=True, kw_only=True)
class NewComicEntity(ComicEntity):
    id: ComicId | None = None  # type: ignore[assignment]
    original_translation_id: TranslationId | None = None  # type: ignore[assignment]
