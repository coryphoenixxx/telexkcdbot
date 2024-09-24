from dataclasses import dataclass
from enum import StrEnum
from functools import cached_property
from pathlib import Path
from typing import Any

import imagesize
from filetype import filetype
from PIL import Image, UnidentifiedImageError

from backend.application.upload.exceptions import (
    UnsupportedImageFormatError,
    UploadedImageReadError,
)
from backend.core.value_objects.base import ValueObject


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
class ImageObj(ValueObject):
    __slots__ = "source", "__dict__"

    source: Path

    @cached_property
    def dimensions(self) -> tuple[int, int]:
        w, h = imagesize.get(self.source)
        if w == -1 or h == -1:
            raise ValueError(f"Unable to retrieve dimensions for {self.source}.")
        return w, h

    @cached_property
    def format(self) -> ImageFormat:
        if kind := self._kind:
            return ImageFormat(kind.extension)
        raise ValueError(f"Unrecognized file format for {self.source}.")

    @cached_property
    def mime(self) -> str:
        if kind := self._kind:
            return str(kind.mime)
        raise ValueError(f"Unrecognized MIME type for {self.source}.")

    @cached_property
    def size(self) -> int:
        return self.source.stat().st_size

    @cached_property
    def _kind(self) -> Any:
        kind = filetype.guess(self.source)
        return kind if kind else None

    def _validate(self) -> None:
        if self.source.exists() is False:
            raise ValueError(f"Image not found for {self.source} path.")

    def validate_securely(self) -> None:
        try:
            with Image.open(self.source) as img:
                img.verify()
        except (UnidentifiedImageError, OSError):
            raise UploadedImageReadError from None

        try:
            _ = self.format
        except ValueError:
            raise UnsupportedImageFormatError(supported_formats=tuple(ImageFormat)) from None
