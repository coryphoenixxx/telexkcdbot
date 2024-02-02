from dataclasses import dataclass

from api.application.comics.types import ComicID
from api.application.images.dtos import TranslationImageResponseDTO
from api.application.translations.dtos.request import TranslationRequestDTO
from api.application.translations.models import TranslationModel
from api.application.translations.types import TranslationID


@dataclass(slots=True)
class TranslationResponseDTO(TranslationRequestDTO):
    id: TranslationID
    comic_id: ComicID
    images: list[TranslationImageResponseDTO]

    @classmethod
    def from_model(cls, model: TranslationModel) -> "TranslationResponseDTO":
        return TranslationResponseDTO(
            id=model.id,
            comic_id=model.comic_id,
            language=model.language,
            title=model.title,
            tooltip=model.tooltip,
            transcript=model.transcript,
            images=[TranslationImageResponseDTO.from_model(img) for img in model.images],
            is_draft=model.is_draft,
        )
