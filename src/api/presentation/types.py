from dataclasses import dataclass
from pathlib import Path

from shared.types import ImageFormat

from api.core.types import Dimensions, Language


@dataclass(slots=True)
class ImageObj:
    path: Path
    fmt: ImageFormat
    dimensions: Dimensions


@dataclass(slots=True)
class TranslationImageMeta:
    number: int | None
    title: str
    language: Language
    is_draft: bool
