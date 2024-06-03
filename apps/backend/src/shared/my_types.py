from enum import StrEnum


class ImageFormat(StrEnum):
    PNG = "png"
    JPG = "jpg"
    WEBP = "webp"
    GIF = "gif"


class Order(StrEnum):
    ASC = "asc"
    DESC = "desc"
