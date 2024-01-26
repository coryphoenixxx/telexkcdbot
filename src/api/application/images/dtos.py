from dataclasses import dataclass
from pathlib import Path

from api.application.images.types import TranslationImageID, TranslationImageVersion
from api.core.types import Dimensions, Language

from .types import ImageFormat


@dataclass(slots=True)
class ImageObj:
    path: Path
    fmt: ImageFormat
    dimensions: Dimensions


@dataclass(slots=True)
class TranslationImageRequestDTO:
    number: int | None
    title: str
    version: TranslationImageVersion
    image: ImageObj
    language: Language
    is_draft: bool


@dataclass(slots=True)
class TranslationImageResponseDTO:
    id: TranslationImageID
    version: TranslationImageVersion
    path: str
    converted_path: str

    def as_dict(self):
        return {
            self.version: {
                "id": self.id,
                "path": self.path,
                "converted": self.converted_path,
            },
        }