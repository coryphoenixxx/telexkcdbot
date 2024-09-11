import shutil
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

import aiofiles
from aiofiles import os as aos

from backend.application.common.interfaces.file_storages import (
    StreamReaderProtocol,
    TempFileManagerInterface,
)
from backend.application.upload.exceptions import (
    UploadImageIsEmptyError,
    UploadImageSizeExceededLimitError,
)
from backend.core.value_objects import TempFileID


@dataclass(slots=True)
class TempFileManager(TempFileManagerInterface):
    temp_dir: Path
    size_limit: int

    async def read_from_stream(
        self,
        stream: StreamReaderProtocol,
        chunk_size: int,
    ) -> TempFileID:
        temp_file_id = self._generate_id()

        async with aiofiles.open(self.temp_dir / str(temp_file_id), "wb") as f:
            file_size = 0

            while chunk := await stream.read(chunk_size):
                file_size += len(chunk)

                if file_size > self.size_limit:
                    raise UploadImageSizeExceededLimitError(self.size_limit)

                await f.write(chunk)

            if file_size == 0:
                raise UploadImageIsEmptyError

            return temp_file_id

    def safe_move(self, path: Path) -> TempFileID:
        file_size = path.stat().st_size

        if file_size == 0:
            raise UploadImageIsEmptyError
        if file_size > self.size_limit:
            raise UploadImageSizeExceededLimitError(self.size_limit)

        temp_file_id = self._generate_id()

        shutil.move(path, self.temp_dir / str(temp_file_id))

        return temp_file_id

    async def remove_by_id(self, temp_file_id: TempFileID) -> None:
        path = self.temp_dir / str(temp_file_id)
        await aos.remove(path)

    def get_abs_path_by_id(self, temp_file_id: TempFileID) -> Path:
        return self.temp_dir / str(temp_file_id)

    def _generate_id(self) -> TempFileID:
        return TempFileID(uuid4())
