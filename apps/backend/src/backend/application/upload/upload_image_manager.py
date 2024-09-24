from dataclasses import dataclass
from pathlib import Path

from backend.application.comic.interfaces import TempFileManagerInterface
from backend.application.common.interfaces.file_storages import StreamReaderProtocol, TempFileID
from backend.core.value_objects import ImageObj


@dataclass(slots=True)
class UploadImageManager:
    temp_file_manager: TempFileManagerInterface

    async def read_from_stream(self, stream: StreamReaderProtocol) -> TempFileID:
        temp_image_id = await self.temp_file_manager.read_from_stream(stream, 1024 * 64)
        ImageObj(source=self.temp_file_manager.get_abs_path(temp_image_id)).validate_securely()

        return temp_image_id

    def read_from_file(self, path: Path) -> TempFileID:
        temp_image_id = self.temp_file_manager.safe_move(path)
        ImageObj(source=self.temp_file_manager.get_abs_path(temp_image_id)).validate_securely()

        return temp_image_id
