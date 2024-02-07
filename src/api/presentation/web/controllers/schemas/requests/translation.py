from pydantic import Field, BaseModel

from api.application.dtos.requests.translation import TranslationRequestDTO
from api.application.types import ComicID, TranslationImageID
from shared.types import LanguageCode


class TranslationRequestSchema(BaseModel):
    comic_id: int
    title: str = Field(min_length=1)
    language: LanguageCode
    tooltip: str | None
    transcript: str | None
    images: list[int]
    is_draft: bool

    def to_dto(self) -> TranslationRequestDTO:
        return TranslationRequestDTO(
            comic_id=ComicID(self.comic_id),
            title=self.title,
            language=self.language,
            tooltip=self.tooltip,
            transcript=self.transcript,
            images=[TranslationImageID(img) for img in self.images],
            is_draft=self.is_draft,
        )
