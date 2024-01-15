from dataclasses import dataclass

from src.app.comics.types import ComicID
from src.app.images.types import TranslationImageID
from src.core.types import Language


@dataclass(slots=True)
class TranslationRequestDTO:
    comic_id: ComicID | None
    title: str
    language: Language
    tooltip: str | None
    transcript: str | None
    news_block: str | None
    images: list[TranslationImageID]
    is_draft: bool
