from enum import StrEnum


class ImageTypeEnum(StrEnum):
    DEFAULT = "default"
    ENLARGED = "enlarged"
    THUMBNAIL = "thumbnail"


class ImageFormatEnum(StrEnum):
    PNG = "png"
    JPG = "jpeg"
    WEBP = "webp"
    GIF = "gif"
