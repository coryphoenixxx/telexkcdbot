from enum import StrEnum


class ComicImageType(StrEnum):
    DEFAULT = "default"
    ENLARGED = "enlarged"
    THUMBNAIL = "thumbnail"


class ImageFormat(StrEnum):
    PNG = "png"
    JPG = "jpeg"
    WEBP = "webp"
    GIF = "gif"
