from dataclasses import dataclass

from api.application.types import ComicID, LanguageCode, TranslationImageID


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
