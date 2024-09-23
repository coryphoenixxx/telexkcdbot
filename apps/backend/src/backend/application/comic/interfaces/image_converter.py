from typing import Protocol

from backend.application.common.dtos import ImageObj


class ImageConverterInterface(Protocol):
    def convert_to_webp(self, original: ImageObj) -> ImageObj: ...
