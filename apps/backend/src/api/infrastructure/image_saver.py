import logging
import shutil
from pathlib import Path
from typing import Final
from uuid import uuid4

import aiofiles.os as aos

from api.application.dtos.common import ImageObj, TranslationImageMeta
from api.core.configs.web import APIConfig
from api.core.utils import slugify


class ImageSaveHelper:
    _IMAGES_URL_PREFIX: Final = "images/comics/"

    def __init__(self, config: APIConfig) -> None:
        self._static_dir = config.static_dir.absolute().resolve()

    async def save(self, meta: TranslationImageMeta, image: ImageObj) -> tuple[Path, Path]:
        rel_path = self._build_rel_path(meta, image)
        abs_path = self._static_dir / rel_path

        await aos.makedirs(abs_path.parent, exist_ok=True)

        try:
            Path(image.path).chmod(0o644)
            shutil.move(image.path, abs_path)
        except FileNotFoundError as err:
            logging.exception("%s: %s", err.strerror, image.path)
            raise

        return abs_path, rel_path

    def cut_rel_path(self, path: Path | None) -> Path | None:
        if path:
            return path.relative_to(self._static_dir)
        return None

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
            logging.error("Invalid meta: %s", meta)

        return self._IMAGES_URL_PREFIX / path
