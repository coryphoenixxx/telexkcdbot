from dataclasses import dataclass
from functools import total_ordering
from pathlib import Path

from src.core.types import LanguageEnum

from .types import ImageTypeEnum, ImageFormatEnum


@dataclass(slots=True)
@total_ordering
class ComicImageDTO:
    issue_number: int | None
    language: LanguageEnum
    path: Path
    type: ImageTypeEnum
    format: ImageFormatEnum
    dimensions: tuple[int, int]

    def __eq__(self, other: "ComicImageDTO"):
        return ((self.dimensions[0] == other.dimensions[0])
                and (self.dimensions[1] == other.dimensions[1]))

    def __lt__(self, other: "ComicImageDTO"):
        return ((self.dimensions[0] < other.dimensions[0])
                and (self.dimensions[1] < other.dimensions[1]))
