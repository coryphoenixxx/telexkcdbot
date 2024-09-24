from pathlib import Path
from typing import NewType, Protocol
from uuid import UUID

from backend.core.value_objects import ImageObj

TempFileID = NewType("TempFileID", UUID)


class StreamReaderProtocol(Protocol):
    async def read(self, chunk_size: int) -> bytes: ...


class TempFileManagerInterface(Protocol):
    async def read_from_stream(
        self,
        stream: StreamReaderProtocol,
        chunk_size: int,
    ) -> TempFileID: ...

    def safe_move(self, path: Path) -> TempFileID: ...

    def get_abs_path(self, temp_file_id: TempFileID) -> Path: ...


class ImageFileManagerInterface(Protocol):
    async def persist(self, image: ImageObj, save_path: Path) -> None: ...
