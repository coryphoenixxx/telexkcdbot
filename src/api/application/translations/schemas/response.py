from api.application.comics.types import ComicID
from api.application.images.schemas import TranslationImageResponseSchema
from api.application.translations.dtos.response import TranslationResponseDTO
from api.application.translations.schemas.request import TranslationRequestSchema
from api.application.translations.types import TranslationID


class TranslationResponseSchema(TranslationRequestSchema):
    id: TranslationID
    comic_id: ComicID
    images: list[TranslationImageResponseSchema]

    @classmethod
    def from_dto(cls, dto: TranslationResponseDTO) -> "TranslationResponseSchema":
        return TranslationResponseSchema(
            id=dto.id,
            comic_id=dto.comic_id,
            title=dto.title,
            tooltip=dto.tooltip,
            transcript=dto.transcript,
            language=dto.language,
            images=[TranslationImageResponseSchema.from_dto(img) for img in dto.images],
            is_draft=dto.is_draft,
        )
