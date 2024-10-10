import shutil
from dataclasses import dataclass
from pathlib import Path

from backend.application.common.interfaces import ImageFileManagerInterface
from backend.domain.value_objects import ImageFileObj


@dataclass(slots=True)
class ImageFSFileManager(ImageFileManagerInterface):
    root_dir: Path

    async def persist(self, image: ImageFileObj, save_path: Path) -> None:
        save_abs_path = self.root_dir / save_path
        save_abs_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(image.source, save_abs_path)

    async def move(self, path_from: Path, path_to: Path) -> None:
        old_abs_path, new_abs_path = self.root_dir / path_from, self.root_dir / path_to
        new_abs_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            shutil.copyfile(old_abs_path, new_abs_path)
        except shutil.SameFileError:
            ...
        else:
            await self.delete(path_from)

    async def delete(self, path: Path) -> None:
        abs_path = self.root_dir / path
        abs_path.unlink()

        current_dir = abs_path.parent
        while current_dir != self.root_dir and not any(current_dir.iterdir()):
            current_dir.rmdir()
            current_dir = current_dir.parent
