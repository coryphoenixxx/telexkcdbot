from enum import StrEnum
from typing import NewType

TranslationImageID = NewType("TranslationImageID", int)


class TranslationImageVersion(StrEnum):
    DEFAULT = "default"
    DOUBLE_SIZE = "x2"
    LARGE = "large"
    THUMBNAIL = "thumb"


class ImageFormat(StrEnum):
    PNG = "png"
    JPG = "jpg"
    WEBP = "webp"
    GIF = "gif"
