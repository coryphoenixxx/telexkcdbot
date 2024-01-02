import os
from pathlib import Path
from typing import Unpack

import filetype
import imagesize
from aiofiles.tempfile import NamedTemporaryFile
from fastapi import HTTPException
from starlette import status
from starlette.datastructures import UploadFile

from src.app.comics.images.dtos import ImageObj
from src.app.comics.images.types import ImageFormat
from src.core.config import settings
from src.core.types import Dimensions


class UploadImageReader:
    _TEMP_DIR: Path = Path('./.tmp')
    _UPLOAD_MAX_SIZE: int = eval(settings.app.upload_max_size)
    _CHUNK_SIZE: int = 1024 * 64
    _SUPPORTED_IMAGE_FORMATS: tuple = tuple(ImageFormat)

    async def read_many(
            self,
            *images: Unpack[UploadFile | None],
    ) -> list[ImageObj | None]:
        return [await self.read_one(img) for img in images]

    async def read_one(self, upload: UploadFile | None):
        if not upload or not upload.filename:
            return None

        tmp_path = await self._read_to_temp(upload)
        return ImageObj(
            path=tmp_path,
            format_=self._get_real_image_format(tmp_path),
            dimensions=Dimensions(*imagesize.get(tmp_path)),
        )

    def _get_real_image_format(self, path: Path) -> ImageFormat:
        try:
            kind = filetype.guess(path)
            if kind is None:
                raise ValueError
            fmt = ImageFormat(kind.extension)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=f"Unsupported image type. Supported: {', '.join(self._SUPPORTED_IMAGE_FORMATS)}",
            )
        return fmt

    async def _read_to_temp(self, file: UploadFile) -> Path:
        os.makedirs(self._TEMP_DIR, exist_ok=True)
        async with NamedTemporaryFile(delete=False, dir=self._TEMP_DIR) as temp:
            file_size = 0
            while chunk := await file.read(self._CHUNK_SIZE):
                file_size += len(chunk)
                if file_size > self._UPLOAD_MAX_SIZE:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"Too large. Max upload size: {self._UPLOAD_MAX_SIZE}.",
                    )
                await temp.write(chunk)
            if file_size == 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="File is empty.",
                )
        return Path(temp.name)
