import shutil
from dataclasses import dataclass
from pathlib import Path

from aiofiles import os as aos

from backend.application.common.dtos import ImageObj
from backend.application.common.interfaces.file_storages import ImageFileManagerInterface


@dataclass(slots=True)
class ImageFSFileManager(ImageFileManagerInterface):
    root_dir: Path

    async def persist(self, image: ImageObj, save_path: Path) -> None:
        save_abs_path = self.root_dir / save_path
        await aos.makedirs(save_abs_path, exist_ok=True)
        shutil.copy(image.source, save_abs_path)

        # TODO: return save abs path?
