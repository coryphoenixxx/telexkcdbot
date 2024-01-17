from dataclasses import dataclass


@dataclass(slots=True)
class Images:
    default: str | None = None
    x2: str | None = None
    large: str | None = None


@dataclass(slots=True)
class XkcdOriginDTO:
    issue_number: int
    xkcd_url: str
    title: str
    publication_date: str
    images: Images
    is_interactive: bool = False
    link_on_click: str | None = None
    tooltip: str | None = None
    news: str | None = None
