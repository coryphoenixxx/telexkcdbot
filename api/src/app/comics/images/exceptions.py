from dataclasses import dataclass
from typing import Any

from fastapi.responses import ORJSONResponse
from starlette import status
from starlette.requests import Request

from src.core.exceptions import BaseAppError


@dataclass
class ImageBadMetadataError(BaseAppError):
    @property
    def detail(self) -> str | dict[str, Any]:
        return "Either the issue number of the comic or its English title should be specified."


@dataclass
class UnsupportedImageFormatError(BaseAppError):
    supported_formats: tuple[str]

    @property
    def detail(self) -> str | dict[str, Any]:
        return {
            "message": "Unsupported image format.",
            "supported_formats": self.supported_formats,
        }


@dataclass
class UploadExceedLimitError(BaseAppError):
    upload_max_size: int

    @property
    def detail(self) -> str | dict[str, Any]:
        return {
            "message": "The uploaded image exceeds the size limit.",
            "upload_max_size": self.upload_max_size,
        }


@dataclass
class UploadFileIsEmpty(BaseAppError):
    @property
    def detail(self) -> str | dict[str, Any]:
        return "File is empty."


def image_bad_metadata_exc_handler(_: Request, exc: ImageBadMetadataError) -> ORJSONResponse:
    return ORJSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=exc.detail,
    )


def unsupported_image_format_exc_handler(
    _: Request,
    exc: UnsupportedImageFormatError,
) -> ORJSONResponse:
    return ORJSONResponse(
        status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        content=exc.detail,
    )


def upload_exceed_limit_exc_handler(_: Request, exc: UploadExceedLimitError) -> ORJSONResponse:
    return ORJSONResponse(
        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
        content=exc.detail,
    )


def upload_file_is_empty_exc_handler(_: Request, exc: UploadFileIsEmpty) -> ORJSONResponse:
    return ORJSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=exc.detail,
    )
