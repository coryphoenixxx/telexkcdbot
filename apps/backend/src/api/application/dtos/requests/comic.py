from dataclasses import dataclass
from datetime import datetime as dt

from api.types import IssueNumber, TranslationImageID


@dataclass(slots=True)
class ComicRequestDTO:
    number: IssueNumber | None
    title: str
    publication_date: dt.date
    tooltip: str
    raw_transcript: str
    xkcd_url: str | None
    explain_url: str | None
    link_on_click: str | None
    is_interactive: bool
    tags: list[str]
    image_ids: list[TranslationImageID]
