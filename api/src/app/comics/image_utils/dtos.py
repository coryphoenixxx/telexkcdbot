from dataclasses import dataclass
from functools import total_ordering
from pathlib import Path

from src.core.types import LanguageEnum

from .types import ImageFormatEnum, ImageTypeEnum


@dataclass(slots=True)
@total_ordering
class ImageDTO:
    path: Path
    format_: ImageFormatEnum
    size: tuple[int, int]

    def __eq__(self, other: "ImageDTO"):
        return (self.size[0] == other.size[0]) and (self.size[1] == other.size[1])

    def __lt__(self, other: "ImageDTO"):
        return (self.size[0] < other.size[0]) and (self.size[1] < other.size[1])

    def is_2x_of(self, other: "ImageDTO"):
        x_diff, y_diff = (self.size[0] - other.size[0] * 2, self.size[1] - other.size[1] * 2)
        return x_diff == y_diff and x_diff <= 5


@dataclass(slots=True)
class ComicImageDTO(ImageDTO):
    issue_number: int | None = None
    language: LanguageEnum = LanguageEnum.EN
    type_: ImageTypeEnum = ImageTypeEnum.DEFAULT

    _IMAGES_DIR_PREFIX: str = "images/comics"

    @property
    def db_path(self) -> str:
        if not self.issue_number:
            raise ValueError
        return f"{self._IMAGES_DIR_PREFIX}/{self.issue_number:04d}/{self.language}/{self.type_}.{self.format_}"
