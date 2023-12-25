import os
from pathlib import Path

import aiofiles.os as aos

from .dtos import ComicImageDTO


class ImageSaver:
    _STATIC_ROOT: Path

    @classmethod
    def setup(cls, static_dir: str):
        cls._STATIC_ROOT = Path(static_dir).absolute()
        os.makedirs(static_dir, exist_ok=True)

    def __init__(self, temp_images: list[ComicImageDTO]):
        self._temp_images = temp_images

    async def save(self):
        for tmp_img in self._temp_images:
            abs_path = self._build_abs_file_path(tmp_img)
            await aos.makedirs(abs_path.parent, exist_ok=True)
            await aos.replace(tmp_img.path, abs_path)

    def _build_abs_file_path(self, temp_image: ComicImageDTO) -> Path:
        return self._STATIC_ROOT / temp_image.rel_path
