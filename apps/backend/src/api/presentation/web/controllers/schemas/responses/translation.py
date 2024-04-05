from collections.abc import Mapping

from pydantic import BaseModel, HttpUrl

from api.application.dtos.responses.translation import TranslationResponseDTO
from api.application.types import LanguageCode, TranslationDraftID
from api.presentation.web.controllers.schemas.responses.image import (
    TranslationImageProcessedResponseSchema,
)


# TODO: sort drafts by created date
class TranslationResponseSchema(BaseModel):
    id: int
    comic_id: int
    title: str
    tooltip: str
    transcript_raw: str
    translator_comment: str
    source_link: HttpUrl | None
    images: list[TranslationImageProcessedResponseSchema]
    draft_ids: list[TranslationDraftID]

    @classmethod
    def from_dto(
        cls,
        dto: TranslationResponseDTO,
    ) -> Mapping[LanguageCode, "TranslationResponseSchema"]:
        return {
            dto.language: TranslationResponseSchema(
                id=dto.id,
                comic_id=dto.comic_id,
                title=dto.title,
                tooltip=dto.tooltip,
                transcript_raw=dto.transcript_raw,
                translator_comment=dto.translator_comment,
                source_link=dto.source_link,
                images=[TranslationImageProcessedResponseSchema.from_dto(img) for img in dto.images],
                draft_ids=[d.id for d in dto.drafts],
            ),
        }


class TranslationWLanguageResponseSchema(TranslationResponseSchema):
    language: LanguageCode

    @classmethod
    def from_dto(
        cls,
        dto: TranslationResponseDTO,
    ) -> "TranslationWLanguageResponseSchema":
        return TranslationWLanguageResponseSchema(
            id=dto.id,
            comic_id=dto.comic_id,
            language=dto.language,
            title=dto.title,
            tooltip=dto.tooltip,
            transcript_raw=dto.transcript_raw,
            translator_comment=dto.translator_comment,
            source_link=dto.source_link,
            images=[TranslationImageProcessedResponseSchema.from_dto(img) for img in dto.images],
            draft_ids=[d.id for d in dto.drafts],
        )
