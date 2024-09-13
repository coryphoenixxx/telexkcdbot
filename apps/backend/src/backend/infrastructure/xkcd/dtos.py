from dataclasses import dataclass
from pathlib import Path
from typing import Annotated

from pydantic import BeforeValidator, HttpUrl
from pydantic.dataclasses import dataclass as pddataclass
from yarl import URL

ExtHttpUrl = Annotated[HttpUrl | URL | str, BeforeValidator(func=lambda x: (HttpUrl(str(x))))]


@pddataclass(slots=True, config={"arbitrary_types_allowed": True, "strict": True})
class XkcdOriginalScrapedData:
    number: int
    publication_date: str
    xkcd_url: ExtHttpUrl
    title: str
    tooltip: str = ""
    click_url: ExtHttpUrl | None = None
    is_interactive: bool = False
    image_path: Path | None = None


@pddataclass(slots=True, config={"arbitrary_types_allowed": True, "strict": True})
class XkcdExplainScrapedData:
    number: int
    explain_url: ExtHttpUrl
    tags: list[str]
    raw_transcript: str


@pddataclass(slots=True, config={"arbitrary_types_allowed": True, "strict": True})
class XkcdTranslationScrapedData:
    number: int
    source_url: ExtHttpUrl | None
    title: str
    language: str
    image_path: Path
    tooltip: str = ""
    raw_transcript: str = ""
    translator_comment: str = ""


@dataclass(slots=True)
class LimitParams:
    start: int
    end: int
    chunk_size: int
    delay: float
