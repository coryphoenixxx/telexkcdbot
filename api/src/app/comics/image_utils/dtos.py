from dataclasses import dataclass
from functools import total_ordering
from pathlib import Path

from src.core.types import LanguageEnum

from .types import ImageFormatEnum, ImageTypeEnum


@dataclass(slots=True)
@total_ordering
class ComicImageDTO:
    issue_number: int | None
    path: Path
    format_: ImageFormatEnum
    dimensions: tuple[int, int]
    language: LanguageEnum = LanguageEnum.EN
    type_: ImageTypeEnum = ImageTypeEnum.DEFAULT

    _IMAGES_DIR_PREFIX: str = "images/comics"

    @property
    def db_path(self) -> str:
        return (
            f"{self._IMAGES_DIR_PREFIX}/"
            f"{self.issue_number:04d}/"
            f"{self.language}/"
            f"{self.type_}.{self.format_}"
        )

    def __eq__(self, other: "ComicImageDTO"):
        return ((self.dimensions[0] == other.dimensions[0])
                and (self.dimensions[1] == other.dimensions[1]))

    def __lt__(self, other: "ComicImageDTO"):
        return ((self.dimensions[0] < other.dimensions[0])
                and (self.dimensions[1] < other.dimensions[1]))
