from dataclasses import dataclass
from datetime import datetime as dt

from api.application.dtos.common import Tag
from api.core.entities import IssueNumber, TranslationImageID


@dataclass(slots=True)
class ComicRequestDTO:
    number: IssueNumber | None
    title: str
    publication_date: dt.date
    tooltip: str
    raw_transcript: str
    xkcd_url: str | None
    explain_url: str | None
    click_url: str | None
    is_interactive: bool
    tags: list[Tag]
    image_ids: list[TranslationImageID]


@dataclass(slots=True)
class TranslationRequestDTO:
    language: str
    title: str
    tooltip: str
    raw_transcript: str
    translator_comment: str
    source_url: str | None
    image_ids: list[TranslationImageID]
    is_draft: bool
