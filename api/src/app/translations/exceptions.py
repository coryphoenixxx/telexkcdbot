from dataclasses import dataclass
from typing import Any

from starlette import status

from src.core.exceptions import BaseAppError
from src.core.types import Language


@dataclass
class TranslationImagesNotCreatedError(BaseAppError):
    image_ids: list[int]
    message: str = "Translation images for these ids were not created."

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
class TranslationTitleUniqueError(BaseAppError):
    title: str
    language: Language
    message: str = "Translation with this title already exists."

    @property
    def status_code(self) -> int:
        return status.HTTP_409_CONFLICT

    @property
    def detail(self) -> str | dict[str, Any]:
        return {
            "message": self.message,
            "title": self.title,
            "language": self.language,
        }
