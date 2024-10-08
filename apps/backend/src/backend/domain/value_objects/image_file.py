from dataclasses import dataclass
from enum import StrEnum
from functools import cached_property
from pathlib import Path
from typing import Any

import imagesize
from filetype import filetype
from PIL import Image, UnidentifiedImageError

from backend.domain.exceptions import BaseAppError


@dataclass(slots=True)
class UnsupportedImageFormatError(BaseAppError):
    supported_formats: tuple[str, ...]

    @property
    def message(self) -> str:
        return f"Unsupported image format. Supported: {', '.join(self.supported_formats)}."


@dataclass(slots=True)
class ImageReadError(BaseAppError):
    @property
    def message(self) -> str:
        return "File is not an image or is corrupted."


class ImageFormat(StrEnum):
    PNG = "png"
    JPG = "jpg"
    WEBP = "webp"
    GIF = "gif"

    @classmethod
    def _missing_(cls, value: Any) -> "ImageFormat | None":
        if value == "jpeg":
            return cls.JPG
        return None


@dataclass(frozen=True)
class ImageFileObj:
    __slots__ = "source", "__dict__"

    source: Path

    @cached_property
    def dimensions(self) -> tuple[int, int]:
        w, h = imagesize.get(self.source)
        if w == -1 or h == -1:
            raise ValueError(f"Unable to retrieve dimensions for {self.source}.")
        return w, h

    @cached_property
    def size(self) -> int:
        return self.source.stat().st_size

    @property
    def format(self) -> ImageFormat:
        if kind := self._kind:
            return ImageFormat(kind.extension)
        raise ValueError(f"Unrecognized file format for {self.source}.")

    @property
    def mime(self) -> str:
        if kind := self._kind:
            return str(kind.mime)
        raise ValueError(f"Unrecognized MIME type for {self.source}.")

    @cached_property
    def _kind(self) -> Any:
        kind = filetype.guess(self.source)
        return kind if kind else None

    def validate_securely(self) -> None:
        try:
            with Image.open(self.source) as img:
                img.verify()
        except (UnidentifiedImageError, OSError):
            raise ImageReadError from None

        try:
            _ = self.dimensions
            _ = self.format
        except ValueError:
            raise UnsupportedImageFormatError(supported_formats=tuple(ImageFormat)) from None
