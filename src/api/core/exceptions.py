from dataclasses import dataclass
from typing import Any

from starlette import status


class BaseAppError(Exception):
    @property
    def status_code(self) -> int:
        raise NotImplementedError

    @property
    def detail(self) -> str | dict[str, Any]:
        raise NotImplementedError


@dataclass
class CreatedEmptySlugError(BaseAppError):
    word: str
    message: str = "Can't slugify this word."

    @property
    def status_code(self):
        return status.HTTP_400_BAD_REQUEST

    @property
    def detail(self) -> str | dict[str, Any]:
        return {
            "message": self.message,
            "word": self.word,
        }
