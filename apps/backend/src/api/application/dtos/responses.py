from dataclasses import dataclass
from datetime import datetime as dt
from pathlib import Path
from typing import TYPE_CHECKING

from shared.utils import cast_or_none

from api.application.dtos.common import Language, TagName
from api.core.value_objects import ComicID, IssueNumber, TagID, TranslationID, TranslationImageID

if TYPE_CHECKING:
    from api.infrastructure.database.models import (
        ComicModel,
        TagModel,
        TranslationImageModel,
        TranslationModel,
    )


@dataclass(slots=True)
class TranslationImageOrphanResponseDTO:
    id: TranslationImageID
    original_rel_path: Path


@dataclass(slots=True)
class TranslationImageResponseDTO:
    id: TranslationImageID
    translation_id: TranslationID
    original_rel_path: Path
    converted_rel_path: Path | None
    thumbnail_rel_path: Path | None

    @classmethod
    def from_model(
        cls,
        model: "TranslationImageModel | None",
    ) -> "TranslationImageResponseDTO | None":
        if model:
            return TranslationImageResponseDTO(
                id=TranslationImageID(model.image_id),
                translation_id=TranslationID(model.translation_id),
                original_rel_path=Path(model.original_rel_path),
                converted_rel_path=cast_or_none(Path, model.converted_rel_path),
                thumbnail_rel_path=cast_or_none(Path, model.thumbnail_rel_path),
            )
        return None


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

    @classmethod
    def from_model(cls, model: "TranslationModel") -> "TranslationResponseDTO":
        return TranslationResponseDTO(
            id=TranslationID(model.translation_id),
            comic_id=ComicID(model.comic_id),
            language=model.language,
            title=model.title,
            tooltip=model.tooltip,
            raw_transcript=model.raw_transcript,
            translator_comment=model.translator_comment,
            image=TranslationImageResponseDTO.from_model(model.image),
            source_url=model.source_url,
            is_draft=model.is_draft,
        )


@dataclass(slots=True)
class TagResponseDTO:
    id: TagID
    name: TagName
    is_blacklisted: bool

    @classmethod
    def from_model(cls, model: "TagModel") -> "TagResponseDTO":
        return TagResponseDTO(
            id=TagID(model.tag_id),
            name=TagName(model.name),
            is_blacklisted=model.is_blacklisted,
        )


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

    @staticmethod
    def _separate_translations(
        translations: list["TranslationModel"],
    ) -> tuple["TranslationModel", list["TranslationModel"]]:
        original_index = None

        for idx, tr in enumerate(translations):
            if tr.language == Language.EN:
                original_index = idx

        original = translations.pop(original_index)

        return original, translations

    @classmethod
    def from_model(cls, model: "ComicModel") -> "ComicResponseDTO":
        original, translations = cls._separate_translations(model.translations)

        return ComicResponseDTO(
            id=ComicID(model.comic_id),
            number=model.number,
            title=original.title,
            translation_id=TranslationID(original.translation_id),
            publication_date=model.publication_date,
            tooltip=original.tooltip,
            xkcd_url=original.source_url,
            explain_url=model.explain_url,
            click_url=model.click_url,
            is_interactive=model.is_interactive,
            tags=[TagResponseDTO.from_model(tag) for tag in model.tags],
            image=TranslationImageResponseDTO.from_model(original.image),
            has_translations=[tr.language for tr in translations],
            translations=[TranslationResponseDTO.from_model(t) for t in translations],
        )
