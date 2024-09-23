import datetime as dt
from dataclasses import dataclass
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
    temp_image_id: TempFileID | None
    is_draft: bool


@dataclass(slots=True, kw_only=True)
class TranslationImageRequestDTO:
    translation_id: TranslationID
    original_path: Path
    converted_path: Path | None = None  # TODO: check


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
    def original_translation(self) -> TranslationRequestDTO:
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
    name: TagName
    is_blacklisted: bool
