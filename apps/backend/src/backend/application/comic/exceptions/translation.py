from dataclasses import dataclass

from backend.application.common.exceptions import BaseAppError
from backend.core.value_objects import Language, TranslationID


@dataclass(slots=True)
class OriginalTranslationOperationForbiddenError(BaseAppError):
    @property
    def message(self) -> str:
        return "Operations on English translation are forbidden."


@dataclass(slots=True)
class TranslationIsAlreadyPublishedError(BaseAppError):
    @property
    def message(self) -> str:
        return "The translation has already been published."


@dataclass(slots=True)
class TranslationAlreadyExistsError(BaseAppError):
    language: Language

    @property
    def message(self) -> str:
        return f"A comic already has a translation into this language ({self.language})."


@dataclass(slots=True)
class TranslationNotFoundError(BaseAppError):
    value: TranslationID | Language

    @property
    def message(self) -> str:
        match self.value:
            case TranslationID():
                return f"Translation (id={self.value.value}) not found."
            case Language():
                return f"Translation (lang={self.value}) not found."
            case _:
                raise ValueError("Invalid type.")
