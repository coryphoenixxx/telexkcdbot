from dataclasses import dataclass

from shared.types import LanguageCode

from api.application.types import ComicID, TranslationImageID


@dataclass(slots=True)
class TranslationRequestDTO:
    comic_id: ComicID
    title: str
    language: LanguageCode
    tooltip: str
    transcript_raw: str
    translator_comment: str
    image_ids: list[TranslationImageID]
    source_link: str | None
    is_draft: bool
