from collections.abc import Mapping

from pydantic import BaseModel, HttpUrl

from api.application.dtos.responses.translation import TranslationResponseDTO
from api.presentation.web.controllers.schemas.responses.image import (
    TranslationImageProcessedResponseSchema,
)
from api.types import Language, TranslationID


class TranslationResponseSchema(BaseModel):
    id: TranslationID
    comic_id: int
    title: str
    tooltip: str
    translator_comment: str
    source_link: HttpUrl | None
    images: list[TranslationImageProcessedResponseSchema]
    is_draft: bool

    @classmethod
    def from_dto(
        cls,
        dto: TranslationResponseDTO,
    ) -> Mapping[Language, "TranslationResponseSchema"]:
        return {
            dto.language: TranslationResponseSchema(
                id=dto.id,
                comic_id=dto.comic_id,
                title=dto.title,
                tooltip=dto.tooltip,
                translator_comment=dto.translator_comment,
                source_link=dto.source_link,
                images=[
                    TranslationImageProcessedResponseSchema.from_dto(img) for img in dto.images
                ],
                is_draft=dto.is_draft,
            ),
        }


class TranslationWLanguageResponseSchema(TranslationResponseSchema):
    language: Language

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
            translator_comment=dto.translator_comment,
            source_link=dto.source_link,
            images=[TranslationImageProcessedResponseSchema.from_dto(img) for img in dto.images],
            is_draft=dto.is_draft,
        )
