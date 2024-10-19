import datetime as dt
from dataclasses import dataclass

from backend.domain.entities import TranslationStatus
from backend.domain.value_objects import Language


@dataclass(slots=True)
class TranslationImageResponseData:
    id: int
    translation_id: int
    image_path: str


@dataclass(slots=True)
class TranslationResponseData:
    id: int
    comic_id: int
    title: str
    language: Language
    tooltip: str
    transcript: str
    translator_comment: str
    source_url: str | None
    image: TranslationImageResponseData | None
    status: TranslationStatus


@dataclass(slots=True)
class TagResponseData:
    id: int
    name: str
    is_visible: bool
    from_explainxkcd: bool


@dataclass(slots=True)
class ComicResponseData:
    id: int
    number: int | None
    publication_date: dt.date
    xkcd_url: str | None
    explain_url: str | None
    click_url: str | None
    translation_id: int
    title: str
    tooltip: str
    is_interactive: bool
    has_translations: list[Language]
    tags: list[TagResponseData]
    image: TranslationImageResponseData | None
    translations: list[TranslationResponseData]


@dataclass(slots=True)
class ComicCompactResponseData:
    id: int
    number: int | None
    publication_date: dt.date
    title: str
    image_url: str | None
