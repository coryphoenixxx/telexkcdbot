from dataclasses import dataclass

from yarl import URL


@dataclass(slots=True)
class XKCDOriginData:
    number: int
    publication_date: str
    xkcd_url: URL
    title: str
    tooltip: str
    link_on_click: URL | None
    is_interactive: bool
    image_url: URL | None


@dataclass(slots=True)
class XKCDExplainData:
    explain_url: URL
    tags: list[str]
    transcript: str


@dataclass(slots=True)
class XKCDFullScrapedData:
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
    transcript: str


@dataclass(slots=True)
class XKCDPOSTData:
    number: int
    publication_date: str
    xkcd_url: URL
    en_title: str
    en_tooltip: str
    link_on_click: URL | None
    is_interactive: bool
    explain_url: URL
    tags: list[str]
    en_transcript: str
    images: list[int]
