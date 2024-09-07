import logging
import shutil
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

import imagesize
from aiofiles import os as aos
from filetype import filetype
from PIL import Image

from backend.core.exceptions.base import BaseAppError
from backend.core.value_objects import IssueNumber, Language, TempFileID
from backend.infrastructure.filesystem.dtos import ImageFormat
from backend.infrastructure.filesystem.temp_file_manager import TempFileManager
from backend.infrastructure.utils import slugify


@dataclass(slots=True)
class TempImageNotFoundError(BaseAppError):
    temp_image_id: str

    @property
    def message(self) -> str:
        return f"A temp image (id=`{self.temp_image_id}`) not found."


@dataclass(frozen=True, slots=True)
class Dimensions:
    width: int
    height: int


@dataclass(frozen=True, slots=True)
class ImageObj:
    path: Path
    fmt: ImageFormat
    dimensions: Dimensions


@dataclass(frozen=True, slots=True)
class TranslationImageMeta:
    number: int | None
    title: str
    language: Language
    is_draft: bool


class TranslationImageFileManager:
    def __init__(
        self,
        static_dir: Path,
        temp_file_manager: TempFileManager,
    ) -> None:
        self._static_dir = static_dir
        self._temp_file_manager = temp_file_manager

    async def save(
        self,
        temp_image_id: TempFileID,
        number: IssueNumber,
        title: str,
        language: Language = Language.EN,
        is_draft: bool = False,
    ) -> Path:
        temp_image_path = self._temp_file_manager.get_abs_path_by_id(temp_image_id)

        if not temp_image_path:
            raise TempImageNotFoundError(str(temp_image_id))

        image = ImageObj(
            path=temp_image_path,
            fmt=ImageFormat(filetype.guess_extension(temp_image_path)),
            dimensions=self._get_dimensions(temp_image_path),
        )

        image_rel_path = self._build_rel_path(
            image=image,
            meta=TranslationImageMeta(number, title, language, is_draft),
        )
        abs_path = self.rel_to_abs(image_rel_path)

        await aos.makedirs(abs_path.parent, exist_ok=True)

        try:
            shutil.move(image.path, abs_path)
        except FileNotFoundError as err:
            logging.exception("%s: %s", err.strerror, image.path)
            raise

        return image_rel_path

    def rel_to_abs(self, path: Path) -> Path:
        return self._static_dir / path

    def abs_to_rel(self, path: Path | None) -> Path | None:
        if path:
            return path.relative_to(self._static_dir)
        return None

    def _get_dimensions(self, path: Path) -> Dimensions:
        w, h = imagesize.get(path)
        if w != -1 and h != -1:
            return Dimensions(width=w, height=h)
        # avif
        with Image.open(path) as image:
            return Dimensions(width=image.width, height=image.height)

    def _build_rel_path(self, image: ImageObj, meta: TranslationImageMeta) -> Path:
        slug = slugify(meta.title)
        uuid_parts = str(uuid4()).split("-")
        random_part = uuid_parts[0] + uuid_parts[1]
        dimensions = f"{image.dimensions.width}x{image.dimensions.height}"

        filename = f"{slug}_{random_part}_{dimensions}.{image.fmt}"

        path = None
        match meta:
            case TranslationImageMeta(number=None, title=t, is_draft=False) if t:
                path = Path(f"extras/{slug}/{meta.language}/{filename}")
            case TranslationImageMeta(number=None, title=t, is_draft=True) if t:
                path = Path(f"extras/{slug}/{meta.language}/drafts/{filename}")
            case TranslationImageMeta(number=n, is_draft=False) if n:
                path = Path(f"{meta.number:05d}/{meta.language}/{filename}")
            case TranslationImageMeta(number=n, is_draft=True) if n:
                path = Path(f"{meta.number:05d}/{meta.language}/drafts/{filename}")

        if not path:
            logging.error("Invalid meta: %s", meta)

        return "images/comics/" / path

    def delete(self, path: Path) -> None:
        abs_path = self.rel_to_abs(path)
        if abs_path.exists():
            Path.unlink(abs_path)
