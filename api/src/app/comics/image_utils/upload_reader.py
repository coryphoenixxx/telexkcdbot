import os
from pathlib import Path

import filetype
import imagesize
from aiofiles.tempfile import NamedTemporaryFile
from fastapi import HTTPException
from starlette import status
from starlette.datastructures import UploadFile

from src.app.comics.image_utils.dtos import ImageDTO
from src.app.comics.image_utils.types import ImageFormatEnum


class UploadImageReader:
    _TEMP_DIR: Path
    _UPLOAD_MAX_SIZE: int
    _CHUNK_SIZE: int = 1024 * 256
    _SUPPORTED_IMAGE_FORMATS: tuple = tuple(fmt.value for fmt in ImageFormatEnum)

    @classmethod
    def setup(cls, upload_max_size: int, temp_dir: str):
        cls._TEMP_DIR = Path(temp_dir)
        cls._UPLOAD_MAX_SIZE = upload_max_size
        os.makedirs(temp_dir, exist_ok=True)

    async def read(self, image: UploadFile | None, image_2x: UploadFile | None) -> tuple[ImageDTO, ImageDTO]:
        image_obj, image_2x_obj = await self.read_one(image), await self.read_one(image_2x)

        if image_obj and image_2x_obj:
            if image_obj >= image_2x_obj:
                image_obj, image_2x_obj = image_2x_obj, image_obj
            if not image_2x_obj.is_2x_of(image_obj):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Images conflict. One image must be 2x from the other.",
                )

        return image_obj, image_2x_obj

    async def read_one(self, upload: UploadFile | None):
        if not upload or not upload.filename:
            return None

        tmp_path = await self._read_to_temp(upload)

        return ImageDTO(
            path=tmp_path,
            format_=self._get_real_image_format(tmp_path),
            size=imagesize.get(tmp_path),
        )

    def _get_real_image_format(self, path: Path) -> ImageFormatEnum:
        try:
            kind = filetype.guess(path)
            if kind is None:
                raise ValueError
            fmt = ImageFormatEnum(kind.extension)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=f"Unsupported image type. Supported: {', '.join(self._SUPPORTED_IMAGE_FORMATS)}",
            )
        return fmt

    async def _read_to_temp(self, file: UploadFile) -> Path:
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
