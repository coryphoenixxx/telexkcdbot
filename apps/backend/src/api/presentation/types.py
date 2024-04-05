from dataclasses import dataclass
from pathlib import Path

from shared.types import ImageFormat

from api.application.types import LanguageCode


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
    language: LanguageCode
    is_draft: bool
