from dataclasses import dataclass

from shared.types import LanguageCode

from api.application.types import ComicID, TranslationImageID


@dataclass(slots=True)
class TranslationRequestDTO:
    comic_id: ComicID | None
    title: str
    language: LanguageCode
    tooltip: str
    transcript_html: str
    translator_comment: str
    images: list[TranslationImageID]
    is_draft: bool
