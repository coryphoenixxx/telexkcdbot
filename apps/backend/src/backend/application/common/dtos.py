from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any

import imagesize
import pillow_avif  # type: ignore[import-untyped] # noqa: F401
from filetype import filetype
from PIL import Image


class ImageFormat(StrEnum):
    PNG = "png"
    JPG = "jpg"
    WEBP = "webp"
    GIF = "gif"
    AVIF = "avif"

    @classmethod
    def _missing_(cls, value: Any) -> "ImageFormat | None":
        if value == "jpeg":
            for member in cls:
                if member.value == "jpg":
                    return member
        return None


@dataclass(slots=True, frozen=True)
class ImageObj:
    source: Path

    @property
    def dimensions(self) -> tuple[int, int]:
        w, h = imagesize.get(self.source)
        if w != -1 and h != -1:
            return w, h

        # avif
        with Image.open(self.source) as image:
            return image.width, image.height

    @property
    def format(self) -> ImageFormat:
        if fmt := filetype.guess_extension(self.source):
            return ImageFormat(fmt)
        raise ValueError(f"Unrecognized file format for {self.source}.")

    @property
    def mime(self) -> str:
        if mime := filetype.guess_mime(self.source):
            return str(mime)
        raise ValueError(f"Unrecognized MIME type for {self.source}.")

    @property
    def size(self) -> int:
        return self.source.stat().st_size
