from pathlib import Path
from typing import Annotated

import pydantic as pyd
from yarl import URL

ExtHttpUrl = Annotated[
    pyd.HttpUrl | URL | str,
    pyd.BeforeValidator(func=lambda x: (pyd.HttpUrl(str(x)))),
]


@pyd.dataclasses.dataclass(slots=True, config={"arbitrary_types_allowed": True, "strict": True})
class XkcdOriginalScrapedData:
    number: int
    publication_date: str
    xkcd_url: ExtHttpUrl
    title: str
    tooltip: str = ""
    click_url: ExtHttpUrl | None = None
    is_interactive: bool = False
    image_path: Path | None = None


@pyd.dataclasses.dataclass(slots=True, config={"arbitrary_types_allowed": True, "strict": True})
class XkcdExplainScrapedData:
    number: int
    explain_url: ExtHttpUrl
    tags: list[str]
    raw_transcript: str


@pyd.dataclasses.dataclass(slots=True, config={"arbitrary_types_allowed": True, "strict": True})
class XkcdTranslationScrapedData:
    number: int
    source_url: ExtHttpUrl | None
    title: str
    language: str
    image_path: Path
    tooltip: str = ""
    raw_transcript: str = ""
    translator_comment: str = ""
