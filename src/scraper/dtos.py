from dataclasses import dataclass

from shared.types import LanguageCode
from yarl import URL


@dataclass(slots=True)
class XkcdBaseScrapedData:
    number: int
    publication_date: str
    xkcd_url: URL
    title: str
    tooltip: str = ""
    link_on_click: URL | None = None
    is_interactive: bool = False
    image_url: URL | None = None


@dataclass(slots=True)
class XkcdScrapedTranslationData:
    number: int
    source_link: URL | None
    title: str
    tooltip: str | None
    image_url: URL | None
    language: LanguageCode
    transcript_raw: str = ""
    translator_comment: str = ""


@dataclass(slots=True)
class XkcdTranslationUploadData:
    comic_id: int
    title: str
    language: LanguageCode
    tooltip: str | None
    transcript_raw: str
    translator_comment: str
    source_link: str | None
    images: list[int]


@dataclass(slots=True)
class XkcdExplainScrapedData:
    explain_url: URL
    tags: list[str]
    transcript_raw: str


@dataclass(slots=True)
class XkcdOriginScrapedData:
    number: int
    publication_date: str
    xkcd_url: URL
    title: str
    tooltip: str
    link_on_click: URL | None
    is_interactive: bool
    image_url: URL | None
    explain_url: URL | None
    tags: list[str]
    transcript_raw: str


@dataclass(slots=True)
class XkcdOriginUploadData:
    number: int
    publication_date: str
    xkcd_url: URL
    en_title: str
    en_tooltip: str
    link_on_click: URL | None
    is_interactive: bool
    explain_url: URL | None
    tags: list[str]
    en_transcript_raw: str
    images: list[int]
