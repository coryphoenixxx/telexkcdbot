import logging
from pathlib import Path
from uuid import uuid4

import filetype
import pillow_avif  # noqa: F401
from filetype import filetype
from PIL import Image, UnidentifiedImageError
from shared.my_types import ImageFormat
from starlette.datastructures import UploadFile

from api.core.exceptions import (
    UnsupportedImageFormatError,
    UploadImageIsNotExistsError,
)
from api.core.exceptions.image import UploadedImageReadError
from api.core.value_objects import TempImageUUID
from api.infrastructure.filesystem.temp_file_manager import FileIsEmptyError, TempFileManager

logger = logging.getLogger(__name__)


class UploadImageManager:
    def __init__(
        self,
        temp_file_manager: TempFileManager,
        supported_formats: tuple[ImageFormat, ...],
    ) -> None:
        self._temp_file_manager = temp_file_manager
        self._supported_formats = supported_formats

    async def read_to_temp(self, upload: UploadFile | None) -> TempImageUUID:
        if upload is None or upload.filename is None:
            raise UploadImageIsNotExistsError

        temp_image_id = TempImageUUID(uuid4())
        temp_filename = str(temp_image_id)

        try:
            try:
                image_path = await self._temp_file_manager.read_from_stream(upload, temp_filename)
            except FileIsEmptyError:
                raise UploadImageIsNotExistsError
            self._validate_format(image_path)
        except Exception:
            await self._temp_file_manager.remove_by_name(temp_filename)
            raise

        return temp_image_id

    def _validate_format(self, path: Path) -> None:
        try:
            Image.open(path)
        except (UnidentifiedImageError, OSError):
            raise UploadedImageReadError

        image_format = filetype.guess_extension(path)
        if image_format not in self._supported_formats:
            raise UnsupportedImageFormatError(
                format=image_format,
                supported_formats=tuple(ImageFormat),
            )
