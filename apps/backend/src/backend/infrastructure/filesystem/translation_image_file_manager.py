import shutil
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

import imagesize
from aiofiles import os as aos
from filetype import filetype
from PIL import Image

from backend.application.common.dtos import ImageFormat
from backend.application.common.interfaces.file_storages import TranslationImageFileManagerInterface
from backend.application.utils import slugify
from backend.core.value_objects import IssueNumber, Language, TempFileID
from backend.infrastructure.filesystem.temp_file_manager import TempFileManager


@dataclass(slots=True)
class Dimensions:
    width: int
    height: int


@dataclass(slots=True)
class ImageObj:
    path: Path
    fmt: ImageFormat
    dimensions: Dimensions


@dataclass(slots=True)
class TranslationImageMeta:
    number: IssueNumber | None
    title: str
    language: Language
    is_draft: bool


@dataclass(slots=True)
class TranslationImageFileManager(TranslationImageFileManagerInterface):
    static_dir: Path
    temp_file_manager: TempFileManager

    async def persist(
        self,
        temp_image_id: TempFileID,
        number: IssueNumber | None,
        title: str,
        language: Language,
        is_draft: bool,
    ) -> Path:
        temp_image_path = self.temp_file_manager.get_abs_path_by_id(temp_image_id)

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

        shutil.move(image.path, abs_path)

        return image_rel_path

    def rel_to_abs(self, path: Path) -> Path:
        return self.static_dir / path

    def abs_to_rel(self, path: Path) -> Path:
        return path.relative_to(self.static_dir)

    def _get_dimensions(self, path: Path) -> Dimensions:
        w, h = imagesize.get(path)
        if w != -1 and h != -1:
            return Dimensions(width=w, height=h)

        # avif
        with Image.open(path) as image:
            return Dimensions(width=image.width, height=image.height)

    def _build_rel_path(self, image: ImageObj, meta: TranslationImageMeta) -> Path:
        slug = slugify(meta.title)
        random_part = uuid4().hex[:8]
        dimensions = f"{image.dimensions.width}x{image.dimensions.height}"

        filename = f"{slug}_{random_part}_{dimensions}.{image.fmt}"

        match meta:
            case TranslationImageMeta(number=None, title=t, is_draft=False) if t:
                path = Path(f"extras/{slug}/{meta.language}/{filename}")
            case TranslationImageMeta(number=None, title=t, is_draft=True) if t:
                path = Path(f"extras/{slug}/{meta.language}/drafts/{filename}")
            case TranslationImageMeta(number=n, is_draft=False) if n is not None:
                path = Path(f"{n.value:05d}/{meta.language}/{filename}")
            case TranslationImageMeta(number=n, is_draft=True) if n is not None:
                path = Path(f"{n.value:05d}/{meta.language}/drafts/{filename}")
            case _:
                raise ValueError("Invalid translation image path metadata.")

        return Path("images/comics/") / path
