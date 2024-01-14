from dataclasses import dataclass

from src.app.images.dtos import TranslationImageResponseDTO
from src.app.translations.dtos.request import TranslationRequestDTO
from src.app.translations.schemas.response import TranslationResponseSchema
from src.app.translations.types import TranslationID


@dataclass(slots=True)
class TranslationResponseDTO(TranslationRequestDTO):
    id: TranslationID
    images: list[TranslationImageResponseDTO]

    def to_schema(self) -> TranslationResponseSchema:
        images_dict = {}
        for image in self.images:
            images_dict = images_dict | image.as_dict()

        return TranslationResponseSchema(
            id=self.id,
            title=self.title,
            language=self.language,
            tooltip=self.tooltip,
            transcript=self.transcript,
            news_block=self.news_block,
            images=images_dict,
            is_draft=self.is_draft,
        )
