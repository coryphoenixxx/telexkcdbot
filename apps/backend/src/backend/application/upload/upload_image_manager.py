from dataclasses import dataclass
from pathlib import Path

import filetype
import pillow_avif  # noqa: F401
from PIL import Image, UnidentifiedImageError

from backend.application.comic.interfaces import TempFileManagerInterface
from backend.application.common.dtos import ImageFormat
from backend.application.common.interfaces.file_storages import StreamReaderProtocol
from backend.application.upload.exceptions import (
    UnsupportedImageFormatError,
    UploadedImageReadError,
)
from backend.core.value_objects import TempFileID


@dataclass(slots=True)
class UploadImageManager:
    temp_file_manager: TempFileManagerInterface
    supported_formats: tuple[ImageFormat, ...]

    async def read_from_stream(self, stream: StreamReaderProtocol) -> TempFileID:
        temp_image_id = await self.temp_file_manager.read_from_stream(stream, 1024 * 64)
        self._validate_format(path=self.temp_file_manager.get_abs_path(temp_image_id))

        return temp_image_id

    def read_from_file(self, path: Path) -> TempFileID:
        temp_image_id = self.temp_file_manager.safe_move(path)
        self._validate_format(path=self.temp_file_manager.get_abs_path(temp_image_id))

        return temp_image_id

    def _validate_format(self, path: Path) -> None:
        try:
            with Image.open(path) as img:
                img.verify()
        except (UnidentifiedImageError, OSError):
            raise UploadedImageReadError from None

        if (image_format := filetype.guess_extension(path)) not in self.supported_formats:
            raise UnsupportedImageFormatError(image_format, self.supported_formats)
