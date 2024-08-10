import logging
import shutil
from pathlib import Path
from uuid import uuid4

import aiofiles
import imagesize
from aiofiles import os as aos
from aiohttp import StreamReader
from filetype import filetype
from shared.my_types import ImageFormat
from starlette.datastructures import UploadFile

from api.application.dtos.common import Dimensions, ImageObj, Language, TranslationImageMeta
from api.core.exceptions import FileIsEmptyError, FileSizeLimitExceededError
from api.core.utils import slugify
from api.core.value_objects import IssueNumber, TempImageID


class ImageFileManager:
    def __init__(
        self,
        temp_dir: Path,
        static_dir: Path,
        size_limit: int,
        chunk_size: int,
    ) -> None:
        self._temp_dir = temp_dir
        self._static_dir = static_dir
        self._size_limit = size_limit
        self._chunk_size = chunk_size

    async def read_to_temp(
        self,
        image_file_obj: StreamReader | UploadFile,
        output_filename: str,
    ) -> Path:
        await aos.makedirs(self._temp_dir, exist_ok=True)

        async with aiofiles.open(self._temp_dir / output_filename, "wb") as f:
            file_size = 0

            while chunk := await image_file_obj.read(self._chunk_size):
                file_size += len(chunk)

                if file_size > self._size_limit:
                    raise FileSizeLimitExceededError(upload_max_size=self._size_limit)

                await f.write(chunk)

            if file_size == 0:
                raise FileIsEmptyError

        return Path(f.name)

    async def remove_temp_by_id(self, temp_image_id: TempImageID) -> None:
        path = self._temp_dir / str(temp_image_id)
        if path.exists():
            await aos.remove(path)

    async def save(
        self,
        number: IssueNumber,
        title: str,
        language: Language,
        is_draft: bool,
        temp_image_id: TempImageID,
    ) -> Path:
        temp_image_path = self.get_temp_path_by_id(temp_image_id)

        image = ImageObj(
            path=temp_image_path,
            fmt=ImageFormat(filetype.guess_extension(temp_image_path)),
            dimensions=Dimensions(*imagesize.get(temp_image_path)),
        )

        rel_path = self._build_rel_path(
            image=image,
            meta=TranslationImageMeta(number, title, language, is_draft),
        )
        abs_path = self.rel_to_abs(rel_path)

        await aos.makedirs(abs_path.parent, exist_ok=True)

        try:
            Path(image.path).chmod(0o644)
            shutil.move(image.path, abs_path)
        except FileNotFoundError as err:
            logging.exception("%s: %s", err.strerror, image.path)
            raise

        return rel_path

    def rel_to_abs(self, path: Path) -> Path:
        return self._static_dir / path

    def abs_to_rel(self, path: Path | None) -> Path | None:
        if path:
            return path.relative_to(self._static_dir)
        return None

    def get_temp_path_by_id(self, temp_image_id: TempImageID) -> Path | None:
        path = self._temp_dir / str(temp_image_id)
        if path.exists():
            return path

    def _build_rel_path(self, image: ImageObj, meta: TranslationImageMeta) -> Path:
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

        return "images/comics/" / path

    def delete(self, path: Path) -> None:
        abs_path = self.rel_to_abs(path)
        if abs_path.exists():
            Path.unlink(abs_path)
