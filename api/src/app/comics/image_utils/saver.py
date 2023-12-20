import os
from functools import cached_property
from pathlib import Path

import aiofiles.os as aos

from .dtos import ComicImageDTO


class ImageSaver:
    _STATIC_ROOT: Path

    def __init__(self, temp_image: ComicImageDTO):
        self.temp_image = temp_image

    @classmethod
    def setup(cls, static_dir: str):
        cls._STATIC_ROOT = Path(static_dir).absolute()
        os.makedirs(static_dir, exist_ok=True)


    @cached_property
    def abs_file_path(self) -> Path:
        return self._STATIC_ROOT / self.temp_image.db_path

    async def save(self):
        await aos.makedirs(self.abs_file_path.parent, exist_ok=True)
        await aos.replace(self.temp_image.path, self.abs_file_path)
