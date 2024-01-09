from pydantic import BaseModel

from src.app.comics.images.types import TranslationImageID, TranslationImageVersion
from src.core.types import Language

from .dtos import TranslationGetDTO
from .types import TranslationID


class TranslationCreateSchema(BaseModel):
    title: str
    tooltip: str | None
    transcript: str | None
    news_block: str | None
    images: list[TranslationImageID]
    language: Language = Language.EN
    is_draft: bool = False


class TranslationGetSchema(BaseModel):
    id: TranslationID
    title: str
    tooltip: str | None
    transcript: str | None
    news_block: str | None
    images: dict[TranslationImageVersion, dict[str, str | None]]
    is_draft: bool

    @classmethod
    def from_dto(cls, dto: TranslationGetDTO):
        return TranslationGetSchema(
            id=dto.id,
            title=dto.title,
            tooltip=dto.tooltip,
            transcript=dto.transcript,
            news_block=dto.news_block,
            is_draft=dto.is_draft,
            images=dto.images,
        )
