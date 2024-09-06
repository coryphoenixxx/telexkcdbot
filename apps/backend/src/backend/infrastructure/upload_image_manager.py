import logging
from dataclasses import dataclass
from pathlib import Path

import filetype
import pillow_avif  # noqa: F401
from PIL import Image, UnidentifiedImageError

from backend.core.exceptions.base import BaseAppError
from backend.core.value_objects import TempFileID
from backend.infrastructure.filesystem.dtos import ImageFormat
from backend.infrastructure.filesystem.temp_file_manager import (
    FileIsEmptyError,
    FileSizeExceededLimitError,
    StreamReaderProtocol,
    TempFileManager,
)

logger = logging.getLogger(__name__)


@dataclass(eq=False, slots=True)
class UploadImageSizeExceededLimitError(BaseAppError):
    limit: int

    @property
    def message(self) -> str:
        return f"The uploaded image file size exceeded the limit ({self.limit / (1024 * 1024)} MB)."


@dataclass(eq=False, slots=True)
class UploadImageIsEmptyError(BaseAppError):
    @property
    def message(self) -> str:
        return "The uploaded image is empty."


@dataclass(eq=False, slots=True)
class UnsupportedImageFormatError(BaseAppError):
    format: str | None
    supported_formats: tuple[ImageFormat, ...]

    @property
    def message(self) -> str:
        return (
            f"Unsupported image format ({self.format}). "
            f"Supported formats: {', '.join(self.supported_formats)}."
        )


@dataclass(eq=False, slots=True)
class UploadedImageReadError(BaseAppError):
    @property
    def message(self) -> str:
        return "The file is not an image or is corrupted."


class UploadImageManager:
    def __init__(
        self,
        temp_file_manager: TempFileManager,
        supported_formats: tuple[ImageFormat, ...],
    ) -> None:
        self._temp_file_manager = temp_file_manager
        self._supported_formats = supported_formats

    async def read_from_stream(self, stream: StreamReaderProtocol) -> TempFileID:
        try:
            temp_image_id = await self._temp_file_manager.read_from_stream(stream, 1024 * 64)
        except FileIsEmptyError:
            raise UploadImageIsEmptyError from None
        except FileSizeExceededLimitError as err:
            raise UploadImageSizeExceededLimitError(limit=err.limit) from None

        self._validate_format(path=self._temp_file_manager.get_abs_path_by_id(temp_image_id))

        return temp_image_id

    def read_from_file(self, path: Path) -> TempFileID:
        try:
            temp_image_id = self._temp_file_manager.safe_move(path)
        except FileIsEmptyError:
            raise UploadImageIsEmptyError from None
        except FileSizeExceededLimitError as err:
            raise UploadImageSizeExceededLimitError(limit=err.limit) from None

        self._validate_format(path=self._temp_file_manager.get_abs_path_by_id(temp_image_id))

        return temp_image_id

    def _validate_format(self, path: Path) -> None:
        try:
            Image.open(path).close()
        except (UnidentifiedImageError, OSError):
            raise UploadedImageReadError from None

        if image_format := filetype.guess_extension(path) not in self._supported_formats:
            raise UnsupportedImageFormatError(image_format, self._supported_formats)
