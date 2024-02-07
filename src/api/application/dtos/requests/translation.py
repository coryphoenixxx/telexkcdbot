from dataclasses import dataclass

from api.application.types import ComicID, TranslationImageID
from shared.types import LanguageCode


@dataclass(slots=True)
class TranslationRequestDTO:
    comic_id: ComicID | None
    title: str
    language: LanguageCode
    tooltip: str | None
    transcript: str | None
    images: list[TranslationImageID]
    is_draft: bool
