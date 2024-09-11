import datetime as dt
from dataclasses import dataclass
from pathlib import Path

from backend.core.value_objects import (
    ComicID,
    IssueNumber,
    Language,
    TagID,
    TagName,
    TranslationID,
    TranslationImageID,
)


@dataclass(slots=True)
class TranslationImageResponseDTO:
    id: TranslationImageID
    translation_id: TranslationID | None
    original: Path
    converted: Path | None


@dataclass(slots=True)
class TranslationResponseDTO:
    id: TranslationID
    comic_id: ComicID
    title: str
    language: Language
    tooltip: str
    raw_transcript: str
    translator_comment: str
    source_url: str | None
    image: TranslationImageResponseDTO | None
    is_draft: bool


@dataclass(slots=True)
class TagResponseDTO:
    id: TagID
    name: TagName
    is_blacklisted: bool


@dataclass(slots=True)
class ComicResponseDTO:
    id: ComicID
    number: IssueNumber | None
    publication_date: dt.date
    explain_url: str | None
    click_url: str | None
    is_interactive: bool
    tags: list[TagResponseDTO]
    has_translations: list[Language]

    translation_id: TranslationID
    xkcd_url: str | None
    title: str
    tooltip: str
    image: TranslationImageResponseDTO | None

    translations: list[TranslationResponseDTO]
