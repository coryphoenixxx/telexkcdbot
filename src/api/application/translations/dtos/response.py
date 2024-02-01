from dataclasses import dataclass

from api.application.comics.types import ComicID
from api.application.images.dtos import TranslationImageResponseDTO
from api.application.images.schemas import TranslationImageResponseSchema
from api.application.translations.dtos.request import TranslationRequestDTO
from api.application.translations.schemas.response import TranslationResponseSchema
from api.application.translations.types import TranslationID


@dataclass(slots=True)
class TranslationResponseDTO(TranslationRequestDTO):
    id: TranslationID
    comic_id: ComicID
    images: list[TranslationImageResponseDTO]

    def to_schema(self) -> TranslationResponseSchema:
        return TranslationResponseSchema(
            id=self.id,
            comic_id=self.comic_id,
            title=self.title,
            language=self.language,
            tooltip=self.tooltip,
            transcript=self.transcript,
            images=[
                TranslationImageResponseSchema(
                    id=img_dto.id,
                    original_rel_path=img_dto.original_rel_path,
                    converted_rel_path=img_dto.converted_rel_path,
                    thumbnail_rel_path=img_dto.thumbnail_rel_path,
                )
                for img_dto in self.images
            ],
            is_draft=self.is_draft,
        )
