from dataclasses import dataclass
from typing import Any

from api.application.dtos.common import Language
from api.core.value_objects import ComicID, TranslationID, TranslationImageID

from .base import (
    BaseBadRequestError,
    BaseConflictError,
    BaseNotFoundError,
)


@dataclass
class ImageNotFoundError(BaseBadRequestError):
    image_id: TranslationImageID
    message: str = "Image not found."

    @property
    def detail(self) -> str | dict[str, Any]:
        return {
            "message": self.message,
            "image_id": self.image_id,
        }


@dataclass
class ImageAlreadyAttachedError(BaseBadRequestError):
    image_id: TranslationImageID
    translation_id: TranslationID
    message: str = "Image already attached to another translation."

    @property
    def detail(self) -> str | dict[str, Any]:
        return {
            "message": self.message,
            "image_id": self.image_id,
            "translation_id": self.translation_id,
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
class TranslationNotFoundError(BaseNotFoundError):
    message: str = "Translation not found."

    @property
    def detail(self) -> str | dict[str, Any]:
        return {"message": self.message}


@dataclass
class OriginalTranslationOperationForbiddenError(BaseBadRequestError):
    message: str = "Operations on English translation are forbidden, use the original."

    @property
    def detail(self) -> str | dict[str, Any]:
        return {"message": self.message}
