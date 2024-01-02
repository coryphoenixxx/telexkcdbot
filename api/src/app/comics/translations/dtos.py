from dataclasses import dataclass

from src.core.types import Language


@dataclass(slots=True)
class TranslationCreateDTO:
    title: str
    tooltip: str | None
    transcript: str | None
    news_block: str | None
    image_ids: list
    language: Language = Language.EN
    is_draft: bool = False


@dataclass(slots=True)
class TranslationGetDTO:
    id: int
    title: str
    tooltip: str | None
    transcript: str | None
    news_block: str | None
    images: dict
    is_draft: bool = False
