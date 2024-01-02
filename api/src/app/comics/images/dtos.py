from dataclasses import dataclass
from pathlib import Path

from src.core.types import Dimensions, Language

from .types import ImageFormat, ImageVersion


@dataclass(slots=True)
class ImageObj:
    path: Path
    format_: ImageFormat
    dimensions: Dimensions


@dataclass(slots=True)
class TranslationImageDTO:
    issue_number: int | None
    en_title: str
    version: ImageVersion
    language: Language
    is_draft: bool
    image_obj: ImageObj
