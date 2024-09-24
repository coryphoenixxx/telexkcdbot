import shutil
from dataclasses import dataclass
from pathlib import Path

from backend.application.common.dtos import ImageObj
from backend.application.common.interfaces.file_storages import ImageFileManagerInterface


@dataclass(slots=True)
class ImageFSFileManager(ImageFileManagerInterface):
    root_dir: Path

    async def persist(self, image: ImageObj, save_path: Path) -> None:
        save_abs_path = self.root_dir / save_path
        save_abs_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(image.source, save_abs_path)

        # TODO: return save abs path?
