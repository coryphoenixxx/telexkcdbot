import shutil
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

import aiofiles

from backend.application.common.exceptions import TempFileNotFoundError
from backend.application.common.interfaces import (
    StreamReaderProtocol,
    TempFileManagerInterface,
)
from backend.application.image.exceptions import ImageIsEmptyError, ImageSizeExceededLimitError
from backend.domain.value_objects.common import TempFileUUID


@dataclass(slots=True)
class TempFileManager(TempFileManagerInterface):
    temp_dir: Path
    size_limit: int

    async def read_from_stream(
        self,
        stream: StreamReaderProtocol,
        chunk_size: int,
    ) -> TempFileUUID:
        temp_file_id = TempFileUUID(uuid4())

        async with aiofiles.open(self.temp_dir / str(temp_file_id.value), "wb") as f:
            file_size = 0

            while chunk := await stream.read(chunk_size):
                file_size += len(chunk)

                if file_size > self.size_limit:
                    raise ImageSizeExceededLimitError(self.size_limit)

                await f.write(chunk)

            if file_size == 0:
                raise ImageIsEmptyError

            return temp_file_id

    def safe_move(self, path: Path) -> TempFileUUID:
        file_size = path.stat().st_size

        if file_size == 0:
            raise ImageIsEmptyError  # TODO: isolate file errors and image errors
        if file_size > self.size_limit:
            raise ImageSizeExceededLimitError(self.size_limit)

        temp_file_id = TempFileUUID(uuid4())

        shutil.move(path, self.temp_dir / str(temp_file_id.value))

        return temp_file_id

    def get_abs_path(self, temp_file_id: TempFileUUID) -> Path:
        if not (abs_path := self.temp_dir / str(temp_file_id.value)).exists():
            raise TempFileNotFoundError(temp_file_id)
        return abs_path
