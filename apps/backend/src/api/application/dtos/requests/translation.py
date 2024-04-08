from dataclasses import dataclass

from api.application.types import Language, TranslationImageID


@dataclass(slots=True)
class TranslationRequestDTO:
    title: str
    language: Language
    tooltip: str
    transcript_raw: str
    translator_comment: str
    image_ids: list[TranslationImageID]
    source_link: str | None
