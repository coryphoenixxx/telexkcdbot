from enum import StrEnum


class ImageFormat(StrEnum):
    PNG = "png"
    JPG = "jpg"
    WEBP = "webp"
    GIF = "gif"
    AVIF = "avif"

    @classmethod
    def _missing_(cls, value: str) -> None:
        if value == "jpeg":
            for member in cls:
                if member.value == "jpg":
                    return member
        return None
