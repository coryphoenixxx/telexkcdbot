from pydantic import BaseModel

from src.app.images.types import TranslationImageID
from src.app.translations.dtos.request import TranslationRequestDTO
from src.core.types import Language


class TranslationRequestSchema(BaseModel):
    title: str
    language: Language
    tooltip: str | None
    transcript: str | None
    news_block: str | None
    images: list[TranslationImageID]
    is_draft: bool = False

    def to_dto(self) -> TranslationRequestDTO:
        return TranslationRequestDTO(
            title=self.title,
            language=self.language,
            tooltip=self.tooltip,
            transcript=self.transcript,
            news_block=self.news_block,
            images=self.images,
            is_draft=self.is_draft,
        )
