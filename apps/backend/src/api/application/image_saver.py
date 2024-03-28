import logging
import shutil
from pathlib import Path
from typing import Final
from uuid import uuid4

import aiofiles.os as aos

from api.presentation.types import ImageObj, TranslationImageMeta
from api.utils import slugify


class ImageSaveHelper:
    _IMAGES_URL_PREFIX: Final = "images/comics/"

    def __init__(self, static_dir: Path):
        self._static_dir = static_dir.absolute().resolve()

    async def save(self, meta: TranslationImageMeta, image: ImageObj) -> tuple[Path, Path]:
        rel_path = self._build_rel_path(meta, image)
        abs_path = self._static_dir / rel_path

        await aos.makedirs(abs_path.parent, exist_ok=True)

        try:
            shutil.move(image.path, abs_path)
        except FileNotFoundError as err:
            logging.error(f"{err.strerror}: {image.path}")
            raise err

        return abs_path, rel_path

    def cut_rel_path(self, path: Path | None):
        if path:
            return path.relative_to(self._static_dir)

    def _build_rel_path(self, meta: TranslationImageMeta, image: ImageObj) -> Path:
        slug = slugify(meta.title)
        uuid_parts = str(uuid4()).split("-")
        random_part = uuid_parts[0] + uuid_parts[1]
        dimensions = f"{image.dimensions.width}x{image.dimensions.height}"

        filename = f"{slug}_{random_part}_{dimensions}_original.{image.fmt}"

        path = None
        match meta:
            case TranslationImageMeta(number=None, title=t, is_draft=False) if t:
                path = Path(f"extras/{slug}/{meta.language}/{filename}")
            case TranslationImageMeta(number=None, title=t, is_draft=True) if t:
                path = Path(f"extras/{slug}/{meta.language}/drafts/{filename}")
            case TranslationImageMeta(number=n, is_draft=False) if n:
                path = Path(f"{meta.number:04d}/{meta.language}/{filename}")
            case TranslationImageMeta(number=n, is_draft=True) if n:
                path = Path(f"{meta.number:04d}/{meta.language}/drafts/{filename}")

        if not path:
            logging.error(f"Invalid meta: {meta}")

        return self._IMAGES_URL_PREFIX / path
