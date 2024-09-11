from backend.application.common.interfaces.file_storages import (
    TempFileManagerInterface,
    TranslationImageFileManagerInterface,
)

from .image_converter import ImageConverterInterface
from .repositories import (
    ComicRepoInterface,
    TagRepoInterface,
    TranslationImageRepoInterface,
    TranslationRepoInterface,
)

__all__ = [
    "TranslationImageFileManagerInterface",
    "TempFileManagerInterface",
    "ComicRepoInterface",
    "TagRepoInterface",
    "TranslationRepoInterface",
    "TranslationImageRepoInterface",
    "ImageConverterInterface",
]
