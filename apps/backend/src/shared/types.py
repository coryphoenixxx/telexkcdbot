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
    UA = "UA"
    NL = "NL"

    @classmethod
    @property
    def translation_languages(cls) -> "tuple[LanguageCode, ...]":
        return tuple(n for n in cls if n != cls.EN)
