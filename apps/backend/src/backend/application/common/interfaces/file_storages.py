from pathlib import Path
from typing import Protocol

from backend.domain.value_objects import ImageFileObj
from backend.domain.value_objects.common import TempFileUUID


class StreamReaderProtocol(Protocol):
    async def read(self, chunk_size: int) -> bytes: ...


class TempFileManagerInterface(Protocol):
    async def read_from_stream(
        self,
        stream: StreamReaderProtocol,
        chunk_size: int,
    ) -> TempFileUUID: ...

    def safe_move(self, path: Path) -> TempFileUUID: ...

    def get_abs_path(self, temp_file_id: TempFileUUID) -> Path: ...


class ImageFileManagerInterface(Protocol):
    async def persist(self, image: ImageFileObj, save_path: Path) -> None: ...

    async def move(self, path_from: Path, path_to: Path) -> None: ...

    async def delete(self, path: Path) -> None: ...
