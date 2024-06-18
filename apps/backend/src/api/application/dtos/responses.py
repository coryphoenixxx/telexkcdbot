from dataclasses import dataclass
from datetime import datetime as dt
from pathlib import Path
from typing import TYPE_CHECKING

from api.application.dtos.common import Language
from api.core.entities import ComicID, IssueNumber, TranslationID, TranslationImageID

if TYPE_CHECKING:
    from api.infrastructure.database.models import (
        ComicModel,
        TranslationImageModel,
        TranslationModel,
    )


@dataclass(slots=True)
class TranslationImageOrphanResponseDTO:
    id: TranslationImageID
    original_rel_path: Path


@dataclass(slots=True)
class TranslationImageProcessedResponseDTO:
    id: TranslationImageID
    translation_id: TranslationID
    original_rel_path: str
    converted_rel_path: str
    thumbnail_rel_path: str

    @classmethod
    def from_model(cls, model: "TranslationImageModel") -> "TranslationImageProcessedResponseDTO":
        return TranslationImageProcessedResponseDTO(
            id=model.image_id,
            translation_id=model.translation_id,
            original_rel_path=model.original_rel_path,
            converted_rel_path=model.converted_rel_path,
            thumbnail_rel_path=model.thumbnail_rel_path,
        )


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
    images: list[TranslationImageProcessedResponseDTO]
    is_draft: bool

    @classmethod
    def from_model(cls, model: "TranslationModel") -> "TranslationResponseDTO":
        return TranslationResponseDTO(
            id=model.translation_id,
            comic_id=model.comic_id,
            language=model.language,
            title=model.title,
            tooltip=model.tooltip,
            raw_transcript=model.raw_transcript,
            translator_comment=model.translator_comment,
            images=[TranslationImageProcessedResponseDTO.from_model(img) for img in model.images],
            source_url=model.source_url,
            is_draft=model.is_draft,
        )


@dataclass(slots=True)
class ComicResponseDTO:
    id: ComicID
    number: IssueNumber | None
    publication_date: dt.date
    explain_url: str | None
    click_url: str | None
    is_interactive: bool
    tags: list[str]
    has_translations: list[Language]

    translation_id: TranslationID
    xkcd_url: str | None
    title: str
    tooltip: str
    images: list[TranslationImageProcessedResponseDTO]

    @classmethod
    def from_model(cls, model: "ComicModel") -> "ComicResponseDTO":
        return ComicResponseDTO(
            id=model.comic_id,
            number=model.number,
            title=model.original.title,
            translation_id=model.original.translation_id,
            publication_date=model.publication_date,
            tooltip=model.original.tooltip,
            xkcd_url=model.original.source_url,
            explain_url=model.explain_url,
            click_url=model.click_url,
            is_interactive=model.is_interactive,
            tags=[tag.name for tag in model.tags],
            images=[
                TranslationImageProcessedResponseDTO.from_model(img)
                for img in model.original.images
            ],
            has_translations=[tr.language for tr in model.translations],
        )


@dataclass(slots=True)
class ComicResponseWTranslationsDTO(ComicResponseDTO):
    translations: list[TranslationResponseDTO]

    @classmethod
    def from_model(cls, model: "ComicModel") -> "ComicResponseWTranslationsDTO":
        return ComicResponseWTranslationsDTO(
            id=model.comic_id,
            number=model.number,
            title=model.original.title,
            translation_id=model.original.translation_id,
            publication_date=model.publication_date,
            tooltip=model.original.tooltip,
            xkcd_url=model.original.source_url,
            explain_url=model.explain_url,
            click_url=model.click_url,
            is_interactive=model.is_interactive,
            tags=sorted([tag.name for tag in model.tags]),
            images=[
                TranslationImageProcessedResponseDTO.from_model(img)
                for img in model.original.images
            ],
            has_translations=[tr.language for tr in model.translations],
            translations=[TranslationResponseDTO.from_model(t) for t in model.translations],
        )
