from dataclasses import dataclass
from typing import Any

from starlette import status

from api.application.types import TranslationID
from api.core.exceptions import BaseAppError
from shared.types import LanguageCode


@dataclass
class TranslationImagesNotCreatedError(BaseAppError):
    image_ids: list[int]
    message: str = "Images were not created."

    @property
    def status_code(self) -> int:
        return status.HTTP_409_CONFLICT

    @property
    def detail(self) -> str | dict[str, Any]:
        return {
            "message": self.message,
            "image_ids": self.image_ids,
        }


@dataclass
class TranslationImagesAlreadyAttachedError(BaseAppError):
    image_ids: list[int]
    translation_ids: list[int]
    message: str = "Images already attached to these translations."

    @property
    def status_code(self) -> int:
        return status.HTTP_409_CONFLICT

    @property
    def detail(self) -> str | dict[str, Any]:
        return {
            "message": self.message,
            "image_ids": self.image_ids,
            "translation_ids": self.translation_ids,
        }


@dataclass
class TranslationUniqueError(BaseAppError):
    comic_id: int
    language: LanguageCode
    message: str = "Comic already has a translation into this language."

    @property
    def status_code(self) -> int:
        return status.HTTP_409_CONFLICT

    @property
    def detail(self) -> str | dict[str, Any]:
        return {
            "message": self.message,
            "comic_id": self.comic_id,
            "language": self.language,
        }


@dataclass
class TranslationImageVersionUniqueError(BaseAppError):
    image_ids: list[int]
    message: str = "The translation should not have multiple images of the same version."

    @property
    def status_code(self) -> int:
        return status.HTTP_409_CONFLICT

    @property
    def detail(self) -> str | dict[str, Any]:
        return {
            "message": self.message,
            "image_ids": self.image_ids,
        }


@dataclass
class TranslationNotFoundError(BaseAppError):
    translation_id: TranslationID
    message: str = "Translation not found."

    @property
    def status_code(self) -> int:
        return status.HTTP_404_NOT_FOUND

    @property
    def detail(self) -> str | dict[str, Any]:
        return {
            "message": self.message,
            "translation_id": self.translation_id,
        }
