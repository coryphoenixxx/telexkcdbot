from dataclasses import dataclass
from pathlib import Path

from api.application.images.models import TranslationImageModel
from api.application.images.types import TranslationImageID
from api.application.translations.types import TranslationID
from api.core.types import Dimensions, Language
from shared.types import ImageFormat


@dataclass(slots=True)
class ImageObj:
    path: Path
    fmt: ImageFormat
    dimensions: Dimensions


@dataclass(slots=True)
class TranslationImageMeta:
    number: int | None
    title: str
    language: Language
    is_draft: bool


@dataclass(slots=True)
class TranslationImageResponseDTO:
    id: TranslationImageID
    translation_id: TranslationID
    original_rel_path: str
    converted_rel_path: str
    thumbnail_rel_path: str

    @classmethod
    def from_model(cls, model: TranslationImageModel):
        return TranslationImageResponseDTO(
            id=model.id,
            translation_id=model.translation_id,
            original_rel_path=model.original_rel_path,
            converted_rel_path=model.converted_rel_path,
            thumbnail_rel_path=model.thumbnail_rel_path,
        )
