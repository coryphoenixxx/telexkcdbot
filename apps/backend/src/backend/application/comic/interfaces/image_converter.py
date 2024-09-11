from pathlib import Path
from typing import Protocol


class ImageConverterInterface(Protocol):
    def convert_to_webp(self, original: Path) -> Path: ...
