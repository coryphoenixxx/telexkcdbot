import asyncio
import os
import time
from pathlib import Path

import aiofiles.os as aos
import magic
from aiofiles.tempfile import NamedTemporaryFile
from fastapi import HTTPException
from PIL import Image
from starlette import status
from starlette.datastructures import UploadFile

from src.core.types import LanguageCode

from .dtos import ComicImageDTO
from .types import ComicImageType, ImageFormat


class ImageReader:
    _TEMP_DIR: Path
    _UPLOAD_MAX_SIZE: int
    _CLEANER: asyncio.Task
    _CLEANER_SLEEP_SEC: int = 60 * 5
    _CLEAN_AFTER_SEC: int = 60
    _CHUNK_SIZE: int = 1024 * 64

    @classmethod
    def setup(cls, upload_max_size: int, temp_dir: str):
        cls._TEMP_DIR = Path(temp_dir)
        cls._UPLOAD_MAX_SIZE = upload_max_size
        os.makedirs(temp_dir, exist_ok=True)

    @classmethod
    async def start_cleaner(cls):
        cls._CLEANER = asyncio.create_task(cls._cleaner())

    @classmethod
    async def _cleaner(cls):
        while True:
            temp_file_list = await aos.listdir(cls._TEMP_DIR)
            if temp_file_list:
                current_time = time.time()
                for temp_file in temp_file_list:
                    path = cls._TEMP_DIR / temp_file
                    if current_time - await aos.path.getatime(path) > cls._CLEAN_AFTER_SEC:
                        await aos.remove(path)
            await asyncio.sleep(cls._CLEANER_SLEEP_SEC)

    async def read(
        self,
        upload: UploadFile | None,
        comic_id: int,
        language: LanguageCode = LanguageCode.EN,
        img_type: ComicImageType = ComicImageType.DEFAULT,
    ) -> ComicImageDTO | None:
        if not upload or not upload.filename:
            return None

        temp_img_path = await self._read_to_temp(upload)
        temp_img_format = self._validate_format(temp_img_path)

        return ComicImageDTO(
            comic_id=comic_id,
            language=language,
            path=temp_img_path,
            type=img_type,
            format=temp_img_format,
            dimensions=Image.open(temp_img_path).size,
        )

    async def _read_to_temp(self, file: UploadFile) -> Path:
        async with NamedTemporaryFile(delete=False, dir=self._TEMP_DIR) as temp:
            file_size = 0
            while chunk := await file.read(self._CHUNK_SIZE):
                file_size += len(chunk)
                if file_size > self._UPLOAD_MAX_SIZE:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"Too large. Max upload size: {self._UPLOAD_MAX_SIZE}",
                    )
                await temp.write(chunk)
        return Path(temp.name)

    @staticmethod
    def _validate_format(filename: Path) -> ImageFormat:
        try:
            fmt = ImageFormat(magic.from_file(filename=filename, mime=True).split("/")[1])
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=f"Unsupported image type. Supported: {', '.join([fmt.value for fmt in ImageFormat])}",
            )

        return fmt
