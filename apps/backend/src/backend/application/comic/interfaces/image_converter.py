from typing import Protocol

from backend.core.value_objects import ImageObj


class ImageConverterInterface(Protocol):
    def convert_to_webp(self, original: ImageObj) -> ImageObj: ...
