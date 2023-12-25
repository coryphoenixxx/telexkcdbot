from enum import StrEnum


class ImageTypeEnum(StrEnum):
    DEFAULT = "default"
    ENLARGED = "2x"
    THUMBNAIL = "thumb"


class ImageFormatEnum(StrEnum):
    PNG = "png"
    JPG = "jpeg"
    WEBP = "webp"
    GIF = "gif"
