from dataclasses import dataclass

from api.application.dtos.responses.image import TranslationImageProcessedResponseDTO
from api.infrastructure.database.models import TranslationModel
from api.my_types import ComicID, Language, TranslationID


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
    def from_model(cls, model: TranslationModel) -> "TranslationResponseDTO":
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
