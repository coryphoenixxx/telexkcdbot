from dataclasses import dataclass
from typing import Any

from .base import BaseAppError, BaseBadRequestError


@dataclass
class UnsupportedImageFormatError(BaseAppError):
    format: str | None
    supported_formats: tuple[str]
    message: str = "Unsupported image format."

    @property
    def detail(self) -> str | dict[str, Any]:
        return {
            "message": self.message,
            "format": self.format,
            "supported_formats": self.supported_formats,
        }


@dataclass
class FileSizeLimitExceededError(BaseAppError):
    upload_max_size: int
    message: str = "The uploaded image exceeds the size limit."

    @property
    def detail(self) -> str | dict[str, Any]:
        return {
            "message": self.message,
            "upload_max_size": self.upload_max_size,
        }


@dataclass
class FileIsEmptyError(BaseBadRequestError):
    message: str = "Request file is empty."

    @property
    def detail(self) -> str | dict[str, Any]:
        return {
            "message": self.message,
        }


@dataclass
class UploadedImageConflictError(BaseBadRequestError):
    message: str = "Either an image url or an image file, not both."

    @property
    def detail(self) -> str | dict[str, Any]:
        return {
            "message": self.message,
        }


@dataclass
class UploadedImageIsNotExistsError(BaseBadRequestError):
    message: str = "Either an image url or an image file must be."

    @property
    def detail(self) -> str | dict[str, Any]:
        return {
            "message": self.message,
        }


@dataclass
class DownloadError(BaseBadRequestError):
    url: str
    message: str = "Couldn't download the image from this URL."

    @property
    def detail(self) -> str | dict[str, Any]:
        return {
            "message": self.message,
            "url": self.url,
        }
