from collections.abc import Mapping

from pydantic import BaseModel, HttpUrl

from api.application.dtos.responses.translation import TranslationResponseDTO
from api.application.types import FlagType, Language, TranslationDraftID, TranslationID
from api.presentation.web.controllers.schemas.responses.image import (
    TranslationImageProcessedResponseSchema,
)


# TODO: sort drafts by created date
class TranslationResponseSchema(BaseModel):
    id: TranslationID
    comic_id: int
    title: str
    tooltip: str
    translator_comment: str
    source_link: HttpUrl | None
    images: list[TranslationImageProcessedResponseSchema]
    draft_ids: list[TranslationDraftID]
    flag: FlagType

    @classmethod
    def from_dto(
        cls,
        dto: TranslationResponseDTO,
    ) -> Mapping[Language, "TranslationResponseSchema"]:
        return {
            dto.language: TranslationResponseSchema(
                id=dto.id,
                comic_id=dto.comic_id,
                flag=Language(dto.language).flag,
                title=dto.title,
                tooltip=dto.tooltip,
                translator_comment=dto.translator_comment,
                source_link=dto.source_link,
                images=[
                    TranslationImageProcessedResponseSchema.from_dto(img) for img in dto.images
                ],
                draft_ids=[d.id for d in dto.drafts],
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
            flag=Language(dto.language).flag,
            title=dto.title,
            tooltip=dto.tooltip,
            translator_comment=dto.translator_comment,
            source_link=dto.source_link,
            images=[TranslationImageProcessedResponseSchema.from_dto(img) for img in dto.images],
            draft_ids=[d.id for d in dto.drafts],
        )


class TranslationDraftResponseSchema(BaseModel):
    id: TranslationDraftID
    original_id: TranslationID
    title: str
    tooltip: str
    translator_comment: str
    source_link: HttpUrl | None
    images: list[TranslationImageProcessedResponseSchema]

    @classmethod
    def from_dto(
        cls,
        dto: TranslationResponseDTO,
    ) -> "TranslationDraftResponseSchema":
        return TranslationDraftResponseSchema(
            id=dto.id,
            original_id=dto.original_id,
            title=dto.title,
            tooltip=dto.tooltip,
            translator_comment=dto.translator_comment,
            source_link=dto.source_link,
            images=[TranslationImageProcessedResponseSchema.from_dto(img) for img in dto.images],
        )
