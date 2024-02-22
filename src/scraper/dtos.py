from dataclasses import dataclass

from shared.types import LanguageCode
from yarl import URL


@dataclass(slots=True)
class XkcdBaseData:
    number: int
    publication_date: str
    xkcd_url: URL
    title: str
    tooltip: str
    link_on_click: URL | None
    is_interactive: bool
    image_url: URL | None


@dataclass(slots=True)
class XkcdTranslation:
    number: int
    source_link: URL | None
    title: str
    tooltip: str | None
    image_url: URL | None
    transcript_raw: str
    translator_comment: str
    language: LanguageCode


@dataclass(slots=True)
class XkcdTranslationPostData:
    comic_id: int
    title: str
    language: LanguageCode
    tooltip: str | None
    transcript_raw: str
    translator_comment: str
    source_link: str | None
    images: list[int]


@dataclass(slots=True)
class XkcdExplainData:
    explain_url: URL
    tags: list[str]
    transcript_raw: str


@dataclass(slots=True)
class XkcdOriginData:
    number: int
    publication_date: str
    xkcd_url: URL
    title: str
    tooltip: str
    link_on_click: URL | None
    is_interactive: bool
    image_url: URL | None
    explain_url: URL
    tags: list[str]
    transcript_raw: str


@dataclass(slots=True)
class XkcdPostData:
    number: int
    publication_date: str
    xkcd_url: URL
    en_title: str
    en_tooltip: str
    link_on_click: URL | None
    is_interactive: bool
    explain_url: URL
    tags: list[str]
    en_transcript_raw: str
    images: list[int]
