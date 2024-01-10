from dataclasses import dataclass
from typing import Any

from starlette import status

from src.core.exceptions import BaseAppError


@dataclass
class ComicNotFoundError(BaseAppError):
    comic_id: int
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
