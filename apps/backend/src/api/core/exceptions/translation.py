from dataclasses import dataclass
from typing import Any

from api.core.value_objects import TranslationID, TranslationImageID

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
    message: str = "A comic already has a translation into this language."

    @property
    def detail(self) -> str | dict[str, Any]:
        return {"message": self.message}


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
