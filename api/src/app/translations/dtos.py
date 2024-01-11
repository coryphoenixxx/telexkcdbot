from dataclasses import dataclass

from src.app.images.dtos import TranslationImageResponseDTO
from src.app.images.types import TranslationImageID
from src.app.translations.types import TranslationID
from src.core.types import Language


@dataclass(slots=True)
class TranslationRequestDTO:
    title: str
    language: Language
    tooltip: str | None
    transcript: str | None
    news_block: str | None
    images: list[TranslationImageID]
    is_draft: bool


@dataclass(slots=True)
class TranslationResponseDTO(TranslationRequestDTO):
    id: TranslationID
    images: list[TranslationImageResponseDTO]
