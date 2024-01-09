from dataclasses import dataclass
from typing import Any

from fastapi.responses import ORJSONResponse
from starlette import status
from starlette.requests import Request

from src.core.exceptions import BaseAppError


@dataclass
class ComicNotFoundError(BaseAppError):
    comic_id: int

    @property
    def detail(self) -> str | dict[str, Any]:
        return {
            "message": "Comic not found.",
            "comic_id": self.comic_id,
        }


def comic_not_found_exc_handler(_: Request, exc: ComicNotFoundError) -> ORJSONResponse:
    return ORJSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content=exc.detail,
    )
