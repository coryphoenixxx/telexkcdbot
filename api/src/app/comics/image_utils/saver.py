from functools import cached_property
from pathlib import Path

import aiofiles.os as aos

from .dtos import ComicImageDTO


class ImageSaver:
    _STATIC_ROOT: Path
    _IMAGES_DIR_PREFIX: str = "images/comics"

    def __init__(self, temp_image_dto: ComicImageDTO):
        self._temp_image_dto = temp_image_dto

    @classmethod
    def setup(cls, static_dir: str):
        cls._STATIC_ROOT = Path(static_dir).absolute()

    @cached_property
    def db_path(self) -> str:
        return (
            f"{self._IMAGES_DIR_PREFIX}/"
            f"{self._temp_image_dto.issue_number}/"
            f"{self._temp_image_dto.language}/"
            f"{self._temp_image_dto.type}.{self._temp_image_dto.format}"
        )

    @cached_property
    def abs_file_path(self) -> Path:
        return self._STATIC_ROOT / self.db_path

    async def save(self):
        await aos.makedirs(self.abs_file_path.parent, exist_ok=True)
        await aos.replace(self._temp_image_dto.path, self.abs_file_path)
