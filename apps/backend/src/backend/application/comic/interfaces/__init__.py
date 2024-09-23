from backend.application.common.interfaces.file_storages import (
    ImageFileManagerInterface,
    TempFileManagerInterface,
)

from .image_converter import ImageConverterInterface
from .repositories import (
    ComicRepoInterface,
    TagRepoInterface,
    TranslationImageRepoInterface,
    TranslationRepoInterface,
)

__all__ = [
    "ImageFileManagerInterface",
    "TempFileManagerInterface",
    "ComicRepoInterface",
    "TagRepoInterface",
    "TranslationRepoInterface",
    "TranslationImageRepoInterface",
    "ImageConverterInterface",
]
