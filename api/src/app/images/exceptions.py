from dataclasses import dataclass
from typing import Any

from starlette import status

from src.core.exceptions import BaseAppError


@dataclass
class UnsupportedImageFormatError(BaseAppError):
    format: str | None
    supported_formats: tuple[str]
    message: str = "Unsupported image format."

    @property
    def status_code(self):
        return status.HTTP_415_UNSUPPORTED_MEDIA_TYPE

    @property
    def detail(self) -> str | dict[str, Any]:
        return {
            "format": self.format,
            "message": self.message,
            "supported_formats": self.supported_formats,
        }


@dataclass
class UploadExceedLimitError(BaseAppError):
    upload_max_size: int
    message: str = "The uploaded image exceeds the size limit."

    @property
    def status_code(self) -> int:
        return status.HTTP_413_REQUEST_ENTITY_TOO_LARGE

    @property
    def detail(self) -> str | dict[str, Any]:
        return {
            "message": self.message,
            "upload_max_size": self.upload_max_size,
        }


@dataclass
class RequestFileIsEmptyError(BaseAppError):
    message: str = "Request file is empty."

    @property
    def status_code(self) -> int:
        return status.HTTP_400_BAD_REQUEST

    @property
    def detail(self) -> str | dict[str, Any]:
        return {"message": self.message}


@dataclass
class OneTypeImageError(BaseAppError):
    message: str = "Either a image url or a image file, not both."

    @property
    def status_code(self) -> int:
        return status.HTTP_409_CONFLICT

    @property
    def detail(self) -> str | dict[str, Any]:
        return {"message": self.message}


@dataclass
class NoImageError(BaseAppError):
    message: str = "Either a image url or a image file must be."

    @property
    def status_code(self) -> int:
        return status.HTTP_400_BAD_REQUEST

    @property
    def detail(self) -> str | dict[str, Any]:
        return {"message": self.message}
