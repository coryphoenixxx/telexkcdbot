from pathlib import Path

import aiofiles.os as aos
import filetype
import imagesize
from aiofiles.tempfile import NamedTemporaryFile
from starlette.datastructures import UploadFile

from src.app.comics.images.dtos import ImageObj
from src.app.comics.images.exceptions import (
    UnsupportedImageFormatError,
    UploadExceedLimitError,
    UploadFileIsEmpty,
)
from src.app.comics.images.types import ImageFormat
from src.core.types import Dimensions


class UploadImageReader:
    _CHUNK_SIZE: int = 1024 * 64

    def __init__(self, tmp_dir: str, upload_max_size: int):
        self._tmp_dir = Path(tmp_dir)
        self._upload_max_size = upload_max_size
        self._supported_formats = tuple(ImageFormat)

    async def read(self, upload: UploadFile | None) -> ImageObj | None:
        if not upload or not upload.filename:
            return None

        tmp_path = await self._read_to_temp(upload)

        return ImageObj(
            path=tmp_path,
            fmt=self._get_real_image_format(tmp_path),
            dimensions=Dimensions(*imagesize.get(tmp_path)),
        )

    def _get_real_image_format(self, path: Path) -> ImageFormat:
        try:
            kind = filetype.guess(path)
            if kind is None:
                raise ValueError
            fmt = ImageFormat(kind.extension)
        except ValueError:
            raise UnsupportedImageFormatError(supported_formats=self._supported_formats)

        return fmt

    async def _read_to_temp(self, file: UploadFile) -> Path:
        await aos.makedirs(self._tmp_dir, exist_ok=True)

        async with NamedTemporaryFile(delete=False, dir=self._tmp_dir) as temp:
            file_size = 0
            while chunk := await file.read(self._CHUNK_SIZE):
                file_size += len(chunk)
                if file_size > self._upload_max_size:
                    raise UploadExceedLimitError(upload_max_size=self._upload_max_size)
                await temp.write(chunk)
            if file_size == 0:
                raise UploadFileIsEmpty

        return Path(temp.name)
