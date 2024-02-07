from api.application.dtos.responses.translation import TranslationResponseDTO
from api.presentation.web.controllers.schemas.requests.translation import (
    TranslationRequestSchema,
)
from api.presentation.web.controllers.schemas.responses.image import (
    TranslationImageFullResponseSchema,
)


class TranslationResponseSchema(TranslationRequestSchema):
    id: int
    comic_id: int
    images: list[TranslationImageFullResponseSchema]

    @classmethod
    def from_dto(cls, dto: TranslationResponseDTO) -> "TranslationResponseSchema":
        return TranslationResponseSchema(
            id=dto.id,
            comic_id=dto.comic_id,
            title=dto.title,
            tooltip=dto.tooltip,
            transcript=dto.transcript,
            language=dto.language,
            images=[TranslationImageFullResponseSchema.from_dto(img) for img in dto.images],
            is_draft=dto.is_draft,
        )
