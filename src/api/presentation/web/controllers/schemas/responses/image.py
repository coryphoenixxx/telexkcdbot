from pydantic import BaseModel

from api.application.dtos.responses.image import TranslationImageFullResponseDTO


class TranslationImageResponseSchema(BaseModel):
    id: int
    original: str


class TranslationImageFullResponseSchema(TranslationImageResponseSchema):
    translation_id: int
    converted: str | None
    thumbnail: str | None

    @classmethod
    def from_dto(cls, dto: TranslationImageFullResponseDTO):
        return TranslationImageFullResponseSchema(
            id=dto.id,
            translation_id=dto.translation_id,
            original=dto.original_rel_path,
            converted=dto.converted_rel_path,
            thumbnail=dto.thumbnail_rel_path,
        )
