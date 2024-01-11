from typing import Any

from pydantic import BaseModel

from src.app.images.types import TranslationImageID, TranslationImageVersion
from src.core.types import Language

from .types import TranslationID


class TranslationRequestSchema(BaseModel):
    title: str
    tooltip: str | None
    transcript: str | None
    news_block: str | None
    images: list[TranslationImageID]
    language: Language
    is_draft: bool = False


class TranslationResponseSchema(TranslationRequestSchema):
    id: TranslationID
    images: dict[TranslationImageVersion, dict[str, Any]]
