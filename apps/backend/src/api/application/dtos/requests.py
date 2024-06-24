from dataclasses import dataclass
from datetime import datetime as dt

from api.application.dtos.common import Language, Tag
from api.core.value_objects import IssueNumber, TranslationImageID


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

    @property
    def original(self) -> TranslationRequestDTO:
        return TranslationRequestDTO(
            language=Language.EN,
            title=self.title,
            tooltip=self.tooltip,
            raw_transcript=self.raw_transcript,
            translator_comment="",
            source_url=self.xkcd_url,
            image_ids=self.image_ids,
            is_draft=False,
        )
