from dataclasses import dataclass, field

from yarl import URL


@dataclass(slots=True)
class Images:
    default: URL | None = None
    x2: URL | None = None
    large: URL | None = None


@dataclass(slots=True)
class XkcdOriginDTO:
    number: int
    publication_date: str
    xkcd_url: URL | str
    title: str
    images: Images = field(default_factory=lambda: Images())
    is_interactive: bool = False
    link_on_click: URL | None = None
    tooltip: str | None = None


@dataclass(slots=True)
class XkcdPostApiDTO(XkcdOriginDTO):
    transcript: str | None = None
    images: list[int] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ExplainXkcdDTO:
    tags: list[str]
    transcript: str | None = None


@dataclass(slots=True)
class AggregatedComicDataDTO:
    origin: XkcdOriginDTO
    explain: ExplainXkcdDTO
