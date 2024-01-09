import logging
from pathlib import Path
from uuid import uuid4

import aiofiles.os as aos
from slugify import slugify

from src.app.comics.images.dtos import TranslationImageCreateDTO


class ImageFileSaver:
    _IMAGES_URL_PREFIX = "images/comics/"

    def __init__(self, static_dir: str):
        self._static_dir = Path(static_dir).absolute()

    async def save(self, img_dto: TranslationImageCreateDTO) -> tuple[Path, Path]:
        rel_saved_path = self._IMAGES_URL_PREFIX / self._build_rel_path(img_dto)

        abs_saved_path = self._static_dir / rel_saved_path

        await aos.makedirs(abs_saved_path.parent, exist_ok=True)
        await aos.replace(img_dto.image.path, abs_saved_path)

        return abs_saved_path, rel_saved_path

    @staticmethod
    def _build_rel_path(dto: TranslationImageCreateDTO) -> Path:
        slug = slugify(dto.en_title, separator="_")
        prefix = str(uuid4()).split('-')[0]
        dimensions = f"{dto.image.dimensions.width}x{dto.image.dimensions.height}"
        filename = f"{slug}_{prefix}_{dimensions}_{dto.version}.{dto.image.fmt}"

        match dto:
            case TranslationImageCreateDTO(issue_number=n, is_draft=False) if n:
                return Path(f"{dto.issue_number:04d}/{dto.language}/{filename}")
            case TranslationImageCreateDTO(issue_number=n, is_draft=True) if n:
                return Path(f"{dto.issue_number:04d}/{dto.language}/drafts/{filename}")
            case TranslationImageCreateDTO(issue_number=None, en_title=t, is_draft=False) if t:
                return Path(f"extras/{slug}/{dto.language}/{filename}")
            case TranslationImageCreateDTO(issue_number=None, en_title=t, is_draft=True) if t:
                return Path(f"extras/{slug}/{dto.language}/drafts/{filename}")
            case _:
                logging.error("Something goes wrong!", dto)