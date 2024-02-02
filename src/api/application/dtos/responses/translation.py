from dataclasses import dataclass

from api.application.dtos.requests.translation import TranslationRequestDTO
from api.application.dtos.responses.image import TranslationImageResponseDTO
from api.application.types import ComicID, TranslationID
from api.infrastructure.database.models import TranslationModel


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
