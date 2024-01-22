from dataclasses import dataclass
from datetime import datetime as dt


@dataclass(slots=True)
class ComicRequestDTO:
    number: int | None
    publication_date: dt.date
    xkcd_url: str | None
    explain_url: str | None
    link_on_click: str | None
    is_interactive: bool
    tags: list[str]
