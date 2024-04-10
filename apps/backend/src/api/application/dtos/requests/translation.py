from dataclasses import dataclass
from typing import Literal

from api.application.types import Language, TranslationID, TranslationImageID


@dataclass(slots=True)
class BaseTranslationRequestDTO:
    title: str
    tooltip: str
    transcript_raw: str
    translator_comment: str
    source_link: str | None
    image_ids: list[TranslationImageID]
    language: Language.NON_ENGLISH
    original_id: TranslationID
    is_draft: bool


@dataclass(slots=True)
class TranslationRequestDTO(BaseTranslationRequestDTO):
    original_id: Literal[None] = None
    is_draft: Literal[False] = False


@dataclass(slots=True)
class TranslationDraftRequestDTO(BaseTranslationRequestDTO):
    original_id: TranslationID | None
    language: Language.NON_ENGLISH | None
    is_draft: Literal[True] = True
