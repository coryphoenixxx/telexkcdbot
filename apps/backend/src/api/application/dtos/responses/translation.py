from dataclasses import dataclass

from api.application.dtos.responses.image import TranslationImageProcessedResponseDTO
from api.application.types import ComicID, LanguageCode, TranslationDraftID, TranslationID
from api.infrastructure.database.models import TranslationModel


@dataclass(slots=True)
class TranslationDraftResponseDTO:
    id: TranslationDraftID
    original_id: TranslationID
    title: str
    tooltip: str
    transcript_raw: str
    translator_comment: str
    source_link: str | None
    images: list[TranslationImageProcessedResponseDTO]

    @classmethod
    def from_model(cls, model: TranslationModel) -> "TranslationDraftResponseDTO":
        return TranslationDraftResponseDTO(
            id=model.translation_id,
            original_id=model.original_id,
            title=model.title,
            tooltip=model.tooltip,
            transcript_raw=model.transcript_raw,
            translator_comment=model.translator_comment,
            images=[TranslationImageProcessedResponseDTO.from_model(img) for img in model.images],
            source_link=model.source_link,
        )


@dataclass(slots=True)
class TranslationResponseDTO:
    id: TranslationID
    comic_id: ComicID
    title: str
    language: LanguageCode
    tooltip: str
    transcript_raw: str
    translator_comment: str
    source_link: str | None
    images: list[TranslationImageProcessedResponseDTO]
    drafts: list[TranslationDraftResponseDTO]

    @classmethod
    def from_model(cls, model: TranslationModel) -> "TranslationResponseDTO":
        return TranslationResponseDTO(
            id=model.translation_id,
            comic_id=model.comic_id,
            language=model.language,
            title=model.title,
            tooltip=model.tooltip,
            transcript_raw=model.transcript_raw,
            translator_comment=model.translator_comment,
            images=[TranslationImageProcessedResponseDTO.from_model(img) for img in model.images],
            source_link=model.source_link,
            drafts=[TranslationDraftResponseDTO.from_model(dr) for dr in model.drafts],
        )
