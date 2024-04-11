from dataclasses import dataclass
from pathlib import Path

from yarl import URL


@dataclass(slots=True)
class XkcdOriginScrapedData:
    number: int
    publication_date: str
    xkcd_url: URL
    title: str
    tooltip: str = ""
    link_on_click: URL | None = None
    is_interactive: bool = False
    image_url: URL | None = None


@dataclass(slots=True)
class XkcdTranslationData:
    number: int
    source_link: URL | None
    title: str
    image: URL | Path | None
    language: str
    tooltip: str = ""
    raw_transcript: str = ""
    translator_comment: str = ""


@dataclass(slots=True)
class XkcdExplanationScrapedBaseData:
    number: int
    explain_url: URL
    tags: list[str]
    raw_transcript: str


@dataclass(slots=True)
class XkcdOriginWithExplainScrapedData:
    number: int | None
    title: str
    publication_date: str
    xkcd_url: URL
    tooltip: str
    link_on_click: URL | None
    is_interactive: bool
    image_url: URL | None
    explain_url: URL | None
    tags: list[str]
    raw_transcript: str


@dataclass(slots=True)
class XkcdOriginUploadData:
    number: int
    title: str
    publication_date: str
    xkcd_url: URL
    explain_url: URL | None
    tooltip: str
    link_on_click: URL | None
    is_interactive: bool
    tags: list[str]
    raw_transcript: str
    image_ids: list[int]


@dataclass(slots=True)
class XkcdTranslationUploadData:
    comic_id: int
    title: str
    language: str
    tooltip: str | None
    raw_transcript: str
    translator_comment: str
    source_link: str | None
    image_ids: list[int]
