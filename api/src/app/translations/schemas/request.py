from pydantic import BaseModel, Field

from src.app.comics.types import ComicID
from src.app.images.types import TranslationImageID
from src.app.translations.dtos.request import TranslationRequestDTO
from src.core.types import Language


class TranslationRequestSchema(BaseModel):
    comic_id: ComicID
    title: str = Field(min_length=1)
    language: Language
    tooltip: str | None
    transcript: str | None
    news: str | None
    images: list[TranslationImageID]
    is_draft: bool

    def to_dto(self) -> TranslationRequestDTO:
        return TranslationRequestDTO(
            comic_id=self.comic_id,
            title=self.title,
            language=self.language,
            tooltip=self.tooltip,
            transcript=self.transcript,
            news=self.news,
            images=self.images,
            is_draft=self.is_draft,
        )
