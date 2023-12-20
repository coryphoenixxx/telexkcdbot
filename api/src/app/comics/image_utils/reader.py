import os
from pathlib import Path

from aiofiles.tempfile import NamedTemporaryFile
from fastapi import HTTPException
from starlette import status
from starlette.datastructures import UploadFile


class ImageReader:
    _TEMP_DIR: Path
    _UPLOAD_MAX_SIZE: int
    _CHUNK_SIZE: int = 1024 * 64

    @classmethod
    def setup(cls, upload_max_size: int, temp_dir: str):
        cls._TEMP_DIR = Path(temp_dir)
        cls._UPLOAD_MAX_SIZE = upload_max_size
        os.makedirs(temp_dir, exist_ok=True)

    async def read(
            self,
            upload: UploadFile | None,
    ) -> Path | None:
        if not upload or not upload.filename:
            return None
        return await self._read_to_temp(upload)

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
