from enum import IntEnum, StrEnum


class ImageFormat(StrEnum):
    PNG = "png"
    JPG = "jpg"
    WEBP = "webp"
    GIF = "gif"
    AVIF = "avif"


class Order(StrEnum):
    ASC = "asc"
    DESC = "desc"


class HTTPStatusCodes(IntEnum):
    HTTP_200_OK = 200
    HTTP_201_CREATED = 201
    HTTP_404_NOT_FOUND = 404
