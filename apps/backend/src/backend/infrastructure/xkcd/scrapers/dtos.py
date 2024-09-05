from dataclasses import dataclass
from datetime import datetime as dt
from pathlib import Path

from yarl import URL


# TODO: pydatic.dataclass
@dataclass(kw_only=True)
class XkcdOriginalScrapedData:
    number: int
    publication_date: dt.date
    xkcd_url: URL
    title: str
    tooltip: str = ""
    click_url: URL | None = None
    is_interactive: bool = False
    image_url: URL | None = None


@dataclass(kw_only=True)
class XkcdExplanationScrapedBaseData:
    number: int
    explain_url: URL
    tags: list[str]
    raw_transcript: str


@dataclass(kw_only=True)
class XkcdOriginalWithExplainScrapedData(
    XkcdOriginalScrapedData,
    XkcdExplanationScrapedBaseData,
): ...


@dataclass(kw_only=True)
class XkcdTranslationDataBase:
    number: int
    source_url: URL | None
    title: str
    language: str
    tooltip: str = ""
    raw_transcript: str = ""
    translator_comment: str = ""


@dataclass(kw_only=True)
class XkcdTranslationScrapedData(XkcdTranslationDataBase):
    image_url: URL | None


@dataclass(kw_only=True)
class XkcdTranslationZippedData(XkcdTranslationDataBase):
    image_path: Path


@dataclass(slots=True)
class LimitParams:
    start: int
    end: int
    chunk_size: int
    delay: int
