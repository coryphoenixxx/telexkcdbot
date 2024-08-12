from dataclasses import dataclass
from typing import Any

from .base import BaseAppError, BaseBadRequestError


@dataclass
class UploadedImageReadError(BaseBadRequestError):
    message: str = "The file is not an image or is corrupted."

    @property
    def detail(self) -> str | dict[str, Any]:
        return {
            "message": self.message,
        }


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
    size_limit: int
    message: str = "The uploaded image exceeds the size limit."

    @property
    def detail(self) -> str | dict[str, Any]:
        return {
            "message": self.message,
            "upload_max_size": self.size_limit,
        }


@dataclass
class UploadImageIsNotExistsError(BaseBadRequestError):
    message: str = "The upload image is empty."

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
