from dataclasses import dataclass
from typing import Any

from api.application.exceptions.base import BaseAppError
from api.application.types import ComicID, LanguageCode, TranslationID, TranslationImageID


@dataclass
class TranslationImagesNotCreatedError(BaseAppError):
    image_ids: list[TranslationImageID]
    message: str = "Images were not created."

    @property
    def detail(self) -> str | dict[str, Any]:
        return {
            "message": self.message,
            "image_ids": self.image_ids,
        }


@dataclass
class TranslationImagesAlreadyAttachedError(BaseAppError):
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
    language: LanguageCode
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
class EnglishTranslationCreateForbiddenError(BaseAppError):
    allowed: list[LanguageCode] = LanguageCode.NON_ENGLISH
    message: str = "Creating an English translation is forbidden."

    @property
    def detail(self) -> str | dict[str, Any]:
        return {
            "message": self.message,
            "allowed": self.allowed,
        }
