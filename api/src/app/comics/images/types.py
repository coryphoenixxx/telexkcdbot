from dataclasses import dataclass
from enum import StrEnum


@dataclass(slots=True)
class ImageInfo:
    size: tuple[int, int] = None
    original: str = None
    converted: str = None


class ImageVersion(StrEnum):
    DEFAULT = "default"
    DOUBLE_SIZE = "2x"
    LARGE = "large"
    THUMBNAIL = "thumb"


class ImageFormat(StrEnum):
    PNG = "png"
    JPG = "jpeg"
    WEBP = "webp"
    GIF = "gif"
