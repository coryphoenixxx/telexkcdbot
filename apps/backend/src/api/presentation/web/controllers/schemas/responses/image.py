from pydantic import BaseModel

from api.application.dtos.responses.image import TranslationImageProcessedResponseDTO


class TranslationImageOrphanResponseSchema(BaseModel):
    id: int
    original: str


class TranslationImageProcessedResponseSchema(TranslationImageOrphanResponseSchema):
    translation_id: int
    converted: str | None
    thumbnail: str | None

    @classmethod
    def from_dto(
        cls,
        dto: TranslationImageProcessedResponseDTO,
    ) -> "TranslationImageProcessedResponseSchema":
        return TranslationImageProcessedResponseSchema(
            id=dto.id,
            translation_id=dto.translation_id,
            original=dto.original_rel_path,
            converted=dto.converted_rel_path,
            thumbnail=dto.thumbnail_rel_path,
        )
