from dataclasses import dataclass
from datetime import datetime as dt


@dataclass(slots=True)
class ComicCreateDTO:
    issue_number: int | None
    publication_date: dt.date
    xkcd_url: str | None
    explain_url: str | None
    reddit_url: str | None
    is_interactive: bool
    is_extra: bool
    link_on_click: str | None
    tags: list[str] | None
