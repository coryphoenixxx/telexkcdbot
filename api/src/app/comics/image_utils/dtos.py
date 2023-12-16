from dataclasses import dataclass
from functools import total_ordering
from pathlib import Path

from src.core.types import LanguageCode

from .types import ComicImageType, ImageFormat


@dataclass(slots=True)
@total_ordering
class ComicImageDTO:
    comic_id: int
    language: LanguageCode
    path: Path
    type: ComicImageType
    format: ImageFormat
    dimensions: tuple[int, int]

    def __eq__(self, other: "ComicImageDTO"):
        return (self.dimensions[0] == other.dimensions[0]) and (self.dimensions[1] == other.dimensions[1])

    def __lt__(self, other: "ComicImageDTO"):
        return (self.dimensions[0] < other.dimensions[0]) and (self.dimensions[1] < other.dimensions[1])
