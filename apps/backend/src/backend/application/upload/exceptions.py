from dataclasses import dataclass

from backend.application.common.exceptions import BaseAppError


@dataclass(slots=True)
class UploadImageSizeExceededLimitError(BaseAppError):
    limit: int

    @property
    def message(self) -> str:
        return f"The uploaded image file size exceeded the limit ({self.limit / (1024 * 1024)} MB)."


@dataclass(slots=True)
class UploadImageIsEmptyError(BaseAppError):
    @property
    def message(self) -> str:
        return "The uploaded image is empty."


@dataclass(slots=True)
class UnsupportedImageFormatError(BaseAppError):
    supported_formats: tuple[str, ...]

    @property
    def message(self) -> str:
        return f"Unsupported image format. Supported formats: {', '.join(self.supported_formats)}."


@dataclass(slots=True)
class UploadedImageReadError(BaseAppError):
    @property
    def message(self) -> str:
        return "The file is not an image or is corrupted."
