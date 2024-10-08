from dataclasses import dataclass
from enum import StrEnum

from backend.domain.exceptions import BaseAppError
from backend.domain.utils import build_searchable_text
from backend.domain.value_objects import (
    ComicId,
    Language,
    PositiveInt,
    TranslationId,
    TranslationTitle,
)


@dataclass(slots=True)
class OriginalTranslationOperationForbiddenError(BaseAppError):
    @property
    def message(self) -> str:
        return "Operations on English translation are forbidden."


class TranslationStatus(StrEnum):
    ON_REVIEW = "ON_REVIEW"
    APPROVED = "APPROVED"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"


@dataclass(slots=True, kw_only=True)
class TranslationEntity:
    id: TranslationId
    comic_id: ComicId
    title: TranslationTitle
    language: Language
    tooltip: str
    transcript: str
    translator_comment: str
    source_url: str | None
    status: TranslationStatus

    def __post_init__(self) -> None:
        if self.language == Language.EN:
            raise OriginalTranslationOperationForbiddenError

    def set_title(self, title: str) -> None:
        self.title = TranslationTitle(title)

    def set_language(self, language: Language) -> None:
        if self.language == Language.EN:
            raise OriginalTranslationOperationForbiddenError
        self.language = language

    @property
    def searchable_text(self) -> str:
        if self.status != TranslationStatus.PUBLISHED:
            return ""

        return build_searchable_text(self.title.value, self.transcript)


@dataclass(slots=True, kw_only=True)
class NewTranslationEntity(TranslationEntity):
    id: PositiveInt | None = None  # type: ignore[assignment]
