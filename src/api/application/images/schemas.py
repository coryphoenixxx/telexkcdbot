from pydantic import BaseModel

from api.application.images.dtos import TranslationImageResponseDTO


class TranslationImageResponseSchema(BaseModel):
    id: int
    translation_id: int
    original: str
    converted: str
    thumbnail: str

    @classmethod
    def from_dto(cls, dto: TranslationImageResponseDTO):
        return TranslationImageResponseSchema(
            id=dto.id,
            translation_id=dto.translation_id,
            original=dto.original_rel_path,
            converted=dto.converted_rel_path,
            thumbnail=dto.thumbnail_rel_path,
        )
