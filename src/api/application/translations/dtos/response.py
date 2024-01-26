from dataclasses import dataclass

from api.application.comics.types import ComicID
from api.application.images.dtos import TranslationImageResponseDTO
from api.application.translations.dtos.request import TranslationRequestDTO
from api.application.translations.schemas.response import TranslationResponseSchema
from api.application.translations.types import TranslationID


@dataclass(slots=True)
class TranslationResponseDTO(TranslationRequestDTO):
    id: TranslationID
    comic_id: ComicID
    images: list[TranslationImageResponseDTO]

    def to_schema(self) -> TranslationResponseSchema:
        images_dict = {}
        for image in self.images:
            images_dict = images_dict | image.as_dict()

        return TranslationResponseSchema(
            id=self.id,
            comic_id=self.comic_id,
            title=self.title,
            language=self.language,
            tooltip=self.tooltip,
            transcript=self.transcript,
            images=images_dict,
            is_draft=self.is_draft,
        )
