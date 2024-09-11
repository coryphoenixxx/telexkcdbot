from pathlib import Path
from typing import Protocol

from backend.core.value_objects import IssueNumber, Language, TempFileID


class StreamReaderProtocol(Protocol):
    async def read(self, chunk_size: int) -> bytes: ...


class TempFileManagerInterface(Protocol):
    async def read_from_stream(
        self,
        stream: StreamReaderProtocol,
        chunk_size: int,
    ) -> TempFileID: ...

    def safe_move(self, path: Path) -> TempFileID: ...

    async def remove_by_id(self, temp_file_id: TempFileID) -> None: ...

    def get_abs_path_by_id(self, temp_file_id: TempFileID) -> Path: ...


class TranslationImageFileManagerInterface(Protocol):
    async def persist(
        self,
        temp_image_id: TempFileID,
        number: IssueNumber | None,
        title: str,
        language: Language,
        is_draft: bool,
    ) -> Path: ...

    def rel_to_abs(self, path: Path) -> Path: ...

    def abs_to_rel(self, path: Path) -> Path: ...
