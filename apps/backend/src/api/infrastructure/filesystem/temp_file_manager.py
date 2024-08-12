from pathlib import Path
from typing import Protocol

import aiofiles
from aiofiles import os as aos

from api.core.exceptions import FileSizeLimitExceededError


class FileIsEmptyError(Exception): ...


class StreamReaderProtocol(Protocol):
    async def read(self, chunk_size: int) -> bytes: ...


class TempFileManager:
    def __init__(
        self,
        temp_dir: Path,
        size_limit: int,
        chunk_size: int,
    ) -> None:
        self._temp_dir = temp_dir
        self._size_limit = size_limit
        self._chunk_size = chunk_size

    async def read_from_stream(self, source: StreamReaderProtocol, filename: str) -> Path:
        async with aiofiles.open(self._temp_dir / filename, "wb") as f:
            file_size = 0

            while chunk := await source.read(self._chunk_size):
                file_size += len(chunk)

                if file_size > self._size_limit:
                    raise FileSizeLimitExceededError(size_limit=self._size_limit)

                await f.write(chunk)

            if file_size == 0:
                raise FileIsEmptyError

            return Path(f.name)

    async def remove_by_name(self, temp_filename: str) -> None:
        path = self._temp_dir / temp_filename
        if path.exists():
            await aos.remove(path)

    def get_abs_path_by_name(self, temp_filename: str) -> Path | None:
        path = self._temp_dir / temp_filename
        if path.exists():
            return path
