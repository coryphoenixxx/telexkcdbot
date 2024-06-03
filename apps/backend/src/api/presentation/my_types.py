from dataclasses import dataclass
from pathlib import Path

from shared.my_types import ImageFormat

from api.my_types import Alpha2LangCode


@dataclass
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
    number: int | None
    title: str
    language: Alpha2LangCode
    is_draft: bool
