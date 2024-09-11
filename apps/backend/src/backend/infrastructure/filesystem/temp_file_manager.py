import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol
from uuid import uuid4

import aiofiles
from aiofiles import os as aos

from backend.core.value_objects import TempFileID


@dataclass(frozen=True, eq=False, slots=True)
class FileIsEmptyError(Exception):
    @property
    def message(self) -> str:
        return "The file is empty."


@dataclass(frozen=True, eq=False, slots=True)
class FileSizeExceededLimitError(Exception):
    limit: int

    @property
    def message(self) -> str:
        return f"The file size exceeded the limit ({self.limit})."


class StreamReaderProtocol(Protocol):
    async def read(self, chunk_size: int) -> bytes: ...


class TempFileManager:
    def __init__(
        self,
        temp_dir: Path,
        size_limit: int,
    ) -> None:
        self._temp_dir = temp_dir
        self._size_limit = size_limit

        self._temp_dir.mkdir(exist_ok=True)

    async def read_from_stream(self, stream: StreamReaderProtocol, chunk_size: int) -> TempFileID:
        temp_file_id = self._generate_id()

        async with aiofiles.open(self._temp_dir / str(temp_file_id), "wb") as f:
            file_size = 0

            while chunk := await stream.read(chunk_size):
                file_size += len(chunk)

                if file_size > self._size_limit:
                    raise FileSizeExceededLimitError(self._size_limit)

                await f.write(chunk)

            if file_size == 0:
                raise FileIsEmptyError

            return temp_file_id

    def safe_move(self, path: Path) -> TempFileID:
        file_size = path.stat().st_size

        if file_size == 0:
            raise FileIsEmptyError
        if file_size > self._size_limit:
            raise FileSizeExceededLimitError(self._size_limit)

        temp_file_id = self._generate_id()

        shutil.move(path, self._temp_dir / str(temp_file_id))

        return temp_file_id

    async def remove_by_id(self, temp_file_id: TempFileID) -> None:
        path = self._temp_dir / str(temp_file_id)
        await aos.remove(path)

    def get_abs_path_by_id(self, temp_file_id: TempFileID) -> Path:
        return self._temp_dir / str(temp_file_id)

    def _generate_id(self) -> TempFileID:
        return TempFileID(uuid4())
