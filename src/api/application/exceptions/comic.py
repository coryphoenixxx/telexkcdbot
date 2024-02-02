from dataclasses import dataclass
from typing import Any

from starlette import status

from api.application.types import ComicID
from api.core.exceptions import BaseAppError


@dataclass
class ComicNotFoundError(BaseAppError):
    comic_id: ComicID
    message: str = "Comic not found."

    @property
    def status_code(self) -> int:
        return status.HTTP_404_NOT_FOUND

    @property
    def detail(self) -> str | dict[str, Any]:
        return {
            "message": self.message,
            "comic_id": self.comic_id,
        }


@dataclass
class ComicByIssueNumberNotFoundError(BaseAppError):
    number: int
    message: str = "Comic with this issue number not found."

    @property
    def status_code(self) -> int:
        return status.HTTP_404_NOT_FOUND

    @property
    def detail(self) -> str | dict[str, Any]:
        return {
            "message": self.message,
            "number": self.number,
        }


@dataclass
class ExtraComicByTitleNotFoundError(BaseAppError):
    title: str
    message: str = "Extra comic with this title not found."

    @property
    def status_code(self) -> int:
        return status.HTTP_404_NOT_FOUND

    @property
    def detail(self) -> str | dict[str, Any]:
        return {
            "message": self.message,
            "title": self.title,
        }


@dataclass
class ComicIssueNumberUniqueError(BaseAppError):
    number: int
    message: str = "Comic with this issue number already exists."

    @property
    def status_code(self) -> int:
        return status.HTTP_409_CONFLICT

    @property
    def detail(self) -> str | dict[str, Any]:
        return {
            "message": self.message,
            "number": self.number,
        }


@dataclass
class ExtraComicSlugUniqueError(BaseAppError):
    title: str
    message: str = "Extra comic with this title already exists."

    @property
    def status_code(self) -> int:
        return status.HTTP_409_CONFLICT

    @property
    def detail(self) -> str | dict[str, Any]:
        return {
            "message": self.message,
            "title": self.title,
        }
