from dataclasses import dataclass
from typing import Any

from api.application.exceptions.base import BaseAppError
from api.application.types import ComicID, Language, TranslationID, TranslationImageID


@dataclass
class ImagesNotCreatedError(BaseAppError):
    image_ids: list[TranslationImageID]
    message: str = "Images were not created."

    @property
    def detail(self) -> str | dict[str, Any]:
        return {
            "message": self.message,
            "image_ids": self.image_ids,
        }


@dataclass
class ImagesAlreadyAttachedError(BaseAppError):
    image_ids: list[TranslationImageID]
    translation_ids: list[TranslationID]
    message: str = "Images already attached to another translations."

    @property
    def detail(self) -> str | dict[str, Any]:
        return {
            "message": self.message,
            "image_ids": self.image_ids,
            "translation_ids": self.translation_ids,
        }


@dataclass
class TranslationAlreadyExistsError(BaseAppError):
    comic_id: ComicID
    language: Language
    message: str = "A comic already has a translation into this language."

    @property
    def detail(self) -> str | dict[str, Any]:
        return {
            "message": self.message,
            "comic_id": self.comic_id,
            "language": self.language,
        }


@dataclass
class TranslationNotFoundError(BaseAppError):
    translation_id: TranslationID
    message: str = "Translation not found."

    @property
    def detail(self) -> str | dict[str, Any]:
        return {
            "message": self.message,
            "translation_id": self.translation_id,
        }


@dataclass
class EnglishTranslationOperationForbiddenError(BaseAppError):
    message: str = "Operations on English translation are forbidden, use the original."

    @property
    def detail(self) -> str | dict[str, Any]:
        return {"message": self.message}


@dataclass
class DraftForDraftCreationError(BaseAppError):
    translation_id: TranslationID
    message: str = "A translation with this id is draft. Creating draft for draft forbidden."

    @property
    def detail(self) -> str | dict[str, Any]:
        return {"message": self.message}
