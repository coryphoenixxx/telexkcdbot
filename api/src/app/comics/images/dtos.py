from dataclasses import dataclass
from pathlib import Path

from src.app.comics.images.types import TranslationImageVersion
from src.core.types import Dimensions, Language

from .models import TranslationImageModel
from .types import ImageFormat


@dataclass(slots=True)
class ImageObj:
    path: Path
    fmt: ImageFormat
    dimensions: Dimensions


@dataclass(slots=True)
class TranslationImageCreateDTO:
    issue_number: int | None
    en_title: str
    version: TranslationImageVersion
    image: ImageObj
    language: Language = Language.EN
    is_draft: bool = False


@dataclass(slots=True)
class TranslationImageGetDTO:
    version: TranslationImageVersion
    path: str
    converted: str

    @classmethod
    def from_model(cls, model: TranslationImageModel):
        return {
            model.version: {
                "path": model.path,
                "converted": model.converted_path,
            },
        }
