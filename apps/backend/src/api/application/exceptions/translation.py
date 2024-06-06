from dataclasses import dataclass
from typing import Any

from api.application.dtos.common import Language
from api.core.entities import ComicID, TranslationID, TranslationImageID

from .base import (
    BaseBadRequestError,
    BaseConflictError,
    BaseNotFoundError,
)


@dataclass
class ImagesNotCreatedError(BaseBadRequestError):
    image_ids: list[TranslationImageID]
    message: str = "Images were not created."

    @property
    def detail(self) -> str | dict[str, Any]:
        return {
            "message": self.message,
            "image_ids": self.image_ids,
        }


@dataclass
class ImagesAlreadyAttachedError(BaseBadRequestError):
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
class TranslationAlreadyExistsError(BaseConflictError):
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
class TranslationByIDNotFoundError(BaseNotFoundError):
    translation_id: TranslationID
    message: str = "Translation not found."

    @property
    def detail(self) -> str | dict[str, Any]:
        return {
            "message": self.message,
            "translation_id": self.translation_id,
        }


@dataclass
class TranslationByLanguageNotFoundError(BaseNotFoundError):
    comic_id: ComicID
    language: Language
    message: str = "Translation not found."

    @property
    def detail(self) -> str | dict[str, Any]:
        return {
            "message": self.message,
            "comic_id": self.comic_id,
        }


@dataclass
class OriginalTranslationOperationForbiddenError(BaseBadRequestError):
    message: str = "Operations on English translation are forbidden, use the original."

    @property
    def detail(self) -> str | dict[str, Any]:
        return {"message": self.message}
