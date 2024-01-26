from pydantic import BaseModel, Field

from api.application.comics.types import ComicID
from api.application.images.types import TranslationImageID
from api.application.translations.dtos.request import TranslationRequestDTO
from api.core.types import Language


class TranslationRequestSchema(BaseModel):
    comic_id: ComicID
    title: str = Field(min_length=1)
    language: Language
    tooltip: str | None
    transcript: str | None
    images: list[TranslationImageID]
    is_draft: bool

    def to_dto(self) -> TranslationRequestDTO:
        return TranslationRequestDTO(
            comic_id=self.comic_id,
            title=self.title,
            language=self.language,
            tooltip=self.tooltip,
            transcript=self.transcript,
            images=self.images,
            is_draft=self.is_draft,
        )
