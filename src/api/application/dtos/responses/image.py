from dataclasses import dataclass

from api.application.types import TranslationID, TranslationImageID
from api.infrastructure.database.models import TranslationImageModel


@dataclass(slots=True)
class TranslationImageResponseDTO:
    id: TranslationImageID
    original_rel_path: str


@dataclass(slots=True)
class TranslationImageFullResponseDTO:
    id: TranslationImageID
    translation_id: TranslationID
    original_rel_path: str
    converted_rel_path: str
    thumbnail_rel_path: str

    @classmethod
    def from_model(cls, model: TranslationImageModel):
        return TranslationImageFullResponseDTO(
            id=model.id,
            translation_id=model.translation_id,
            original_rel_path=model.original_rel_path,
            converted_rel_path=model.converted_rel_path,
            thumbnail_rel_path=model.thumbnail_rel_path,
        )
