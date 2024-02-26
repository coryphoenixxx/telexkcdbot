from enum import StrEnum


class ImageFormat(StrEnum):
    PNG = "png"
    JPG = "jpg"
    WEBP = "webp"
    GIF = "gif"


class LanguageCode(StrEnum):
    EN = "EN"
    RU = "RU"
    CN = "CN"
    ES = "ES"
    DE = "DE"
    FR = "FR"