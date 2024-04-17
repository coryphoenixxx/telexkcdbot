from dataclasses import dataclass

from api.types import TranslationImageID


@dataclass(slots=True)
class TranslationRequestDTO:
    language: str
    title: str
    tooltip: str
    raw_transcript: str
    translator_comment: str
    source_url: str | None
    image_ids: list[TranslationImageID]
    is_draft: bool
