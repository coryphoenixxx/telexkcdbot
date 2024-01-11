from dataclasses import dataclass
from typing import Any

from starlette import status

from src.core.exceptions import BaseAppError


@dataclass
class UnsupportedImageFormatError(BaseAppError):
    supported_formats: tuple[str]
    message: str = "Unsupported image format."

    @property
    def status_code(self):
        return status.HTTP_415_UNSUPPORTED_MEDIA_TYPE

    @property
    def detail(self) -> str | dict[str, Any]:
        return {
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
