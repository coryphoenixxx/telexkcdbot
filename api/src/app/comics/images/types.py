from enum import StrEnum
from typing import NewType

TranslationImageID = NewType("TranslationImageID", int)


class TranslationImageVersion(StrEnum):
    DEFAULT = "default"
    DOUBLE_SIZE = "2x"
    LARGE = "large"
    THUMBNAIL = "thumb"


class ImageFormat(StrEnum):
    PNG = "png"
    JPG = "jpeg"
    WEBP = "webp"
    GIF = "gif"
