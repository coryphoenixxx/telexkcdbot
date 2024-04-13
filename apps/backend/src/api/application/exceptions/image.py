from dataclasses import dataclass
from typing import Any

from api.application.exceptions.base import BaseAppError, BaseBadRequestError


@dataclass
class UnsupportedImageFormatError(BaseAppError):
    invalid_format: str | None
    supported_formats: tuple[str]
    message: str = "Unsupported image format."

    @property
    def detail(self) -> str | dict[str, Any]:
        return {
            "message": self.message,
            "format": self.invalid_format,
            "supported_formats": self.supported_formats,
        }


@dataclass
class UploadExceedSizeLimitError(BaseAppError):
    upload_max_size: int
    message: str = "The uploaded image exceeds the size limit."

    @property
    def detail(self) -> str | dict[str, Any]:
        return {
            "message": self.message,
            "upload_max_size": self.upload_max_size,
        }


@dataclass
class RequestFileIsEmptyError(BaseBadRequestError):
    message: str = "Request file is empty."

    @property
    def detail(self) -> str | dict[str, Any]:
        return {
            "message": self.message,
        }


@dataclass
class UploadedImageTypeConflictError(BaseBadRequestError):
    message: str = "Either an image url or an image file, not both."

    @property
    def detail(self) -> str | dict[str, Any]:
        return {
            "message": self.message,
        }


@dataclass
class UploadedImageError(BaseBadRequestError):
    message: str = "Either an image url or an image file must be."

    @property
    def detail(self) -> str | dict[str, Any]:
        return {
            "message": self.message,
        }


@dataclass
class DownloadingImageError(BaseBadRequestError):
    url: str
    message: str = "Couldn't download the image from this URL."

    @property
    def detail(self) -> str | dict[str, Any]:
        return {
            "message": self.message,
            "url": self.url,
        }
