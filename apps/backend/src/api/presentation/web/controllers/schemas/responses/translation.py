from api.application.dtos.responses.translation import TranslationResponseDTO
from api.presentation.web.controllers.schemas.requests.translation import (
    TranslationRequestSchema,
)
from api.presentation.web.controllers.schemas.responses.image import (
    TranslationImageWithPathsResponseSchema,
)


class TranslationResponseSchema(TranslationRequestSchema):
    id: int
    comic_id: int
    images: list[TranslationImageWithPathsResponseSchema]

    @classmethod
    def from_dto(cls, dto: TranslationResponseDTO) -> "TranslationResponseSchema":
        return TranslationResponseSchema(
            id=dto.id,
            comic_id=dto.comic_id,
            title=dto.title,
            tooltip=dto.tooltip,
            transcript_raw=dto.transcript_raw,
            translator_comment=dto.translator_comment,
            language=dto.language,
            images=[TranslationImageWithPathsResponseSchema.from_dto(img) for img in dto.images],
            source_link=dto.source_link,
            is_draft=dto.is_draft,
        )
