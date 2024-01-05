from dataclasses import dataclass
from typing import Any

from fastapi.responses import ORJSONResponse
from starlette import status
from starlette.requests import Request

from src.core.exceptions import BaseAppException


@dataclass
class TranslationImagesNotCreatedError(BaseAppException):
    image_ids: list[int]

    @property
    def detail(self) -> str | dict[str, Any]:
        return {
            "message": "Translation images for these ids were not created.",
            "image_ids": self.image_ids,
        }


def translation_images_not_found_exc_handler(_: Request, exc: TranslationImagesNotCreatedError) -> ORJSONResponse:
    return ORJSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content=exc.detail,
    )
