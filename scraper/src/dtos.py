from dataclasses import dataclass, field


@dataclass(slots=True)
class Images:
    default: str | None = None
    x2: str | None = None
    large: str | None = None


@dataclass(slots=True)
class XkcdOriginDTO:
    issue_number: int
    publication_date: str
    xkcd_url: str
    title: str
    images: Images
    is_interactive: bool = False
    link_on_click: str | None = None
    tooltip: str | None = None
    news: str | None = None


@dataclass(slots=True)
class XkcdCompleteDTO(XkcdOriginDTO):
    transcript: str | None = None
    images: list[int] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
