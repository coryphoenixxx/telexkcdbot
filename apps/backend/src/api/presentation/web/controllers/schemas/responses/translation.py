from collections.abc import Mapping

from pydantic import BaseModel, HttpUrl

from api.application.dtos.responses.translation import TranslationResponseDTO
from api.my_types import Language, TranslationID
from api.presentation.web.controllers.schemas.responses.image import (
    TranslationImageProcessedResponseSchema,
)


class TranslationResponseSchema(BaseModel):
    id: TranslationID
    comic_id: int
    title: str
    tooltip: str
    translator_comment: str
    source_url: HttpUrl | None
    images: list[TranslationImageProcessedResponseSchema]

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
                source_url=dto.source_url,
                images=[
                    TranslationImageProcessedResponseSchema.from_dto(img) for img in dto.images
                ],
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
            source_url=dto.source_url,
            images=[TranslationImageProcessedResponseSchema.from_dto(img) for img in dto.images],
        )


class TranslationWDraftStatusSchema(TranslationWLanguageResponseSchema):
    is_draft: bool

    @classmethod
    def from_dto(
        cls,
        dto: TranslationResponseDTO,
    ) -> "TranslationWDraftStatusSchema":
        return TranslationWDraftStatusSchema(
            id=dto.id,
            comic_id=dto.comic_id,
            language=dto.language,
            title=dto.title,
            tooltip=dto.tooltip,
            translator_comment=dto.translator_comment,
            source_url=dto.source_url,
            images=[TranslationImageProcessedResponseSchema.from_dto(img) for img in dto.images],
            is_draft=dto.is_draft,
        )
