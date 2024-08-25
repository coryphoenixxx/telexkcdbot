from dataclasses import dataclass
from datetime import datetime as dt
from pathlib import Path
from typing import TypedDict

from backend.core.value_objects import IssueNumber, Language, TagName, TempFileID, TranslationID


@dataclass(slots=True, kw_only=True)
class TranslationRequestDTO:
    language: Language
    title: str
    tooltip: str
    raw_transcript: str
    translator_comment: str
    source_url: str | None
    temp_image_id: TempFileID
    is_draft: bool


@dataclass(slots=True, kw_only=True)
class TranslationImageRequestDTO:
    translation_id: TranslationID
    original: Path
    converted: Path | None = None


@dataclass(slots=True, kw_only=True)
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
    tags: list[TagName]
    temp_image_id: TempFileID | None

    @property
    def original(self) -> TranslationRequestDTO:
        return TranslationRequestDTO(
            language=Language.EN,
            title=self.title,
            tooltip=self.tooltip,
            raw_transcript=self.raw_transcript,
            translator_comment="",
            source_url=self.xkcd_url,
            temp_image_id=self.temp_image_id,
            is_draft=False,
        )


class TagUpdateDTO(TypedDict, total=False):
    name: str
    is_blacklisted: bool
