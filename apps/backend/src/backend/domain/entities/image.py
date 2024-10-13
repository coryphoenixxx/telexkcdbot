from dataclasses import dataclass
from enum import IntEnum, StrEnum
from pathlib import Path
from typing import Any

from backend.domain.value_objects import ImageId, PositiveInt, TempFileUUID
from backend.domain.value_objects.image_file import ImageFormat


class ImageLinkType(StrEnum):
    TRANSLATION = "TRANSLATION"
    USER = "USER"


class ImageProcessStage(IntEnum):
    ORPHAN = 0
    CREATED = 1
    CONVERTED = 2
    ENLARGED = 3


@dataclass(slots=True)
class ImageMeta:
    format: ImageFormat
    dimensions: tuple[int, int]
    size: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "format": self.format,
            "dimensions": self.dimensions,
            "size": self.size,
        }


@dataclass(slots=True, kw_only=True)
class ImageEntity:
    id: ImageId
    temp_image_id: TempFileUUID | None
    link_type: ImageLinkType | None = None
    link_id: PositiveInt | None = None
    original_path: Path | None = None
    converted_path: Path | None = None
    x2_path: Path | None = None
    position_number: int | None = None
    meta: ImageMeta
    is_deleted: bool = False

    def has_another_owner(self, link_type: ImageLinkType, link_id: PositiveInt) -> bool:
        if self.link_type and self.link_id:
            return (self.link_type, self.link_id.value) != (link_type, link_id.value)
        return False

    def create(
        self,
        link_type: ImageLinkType,
        link_id: PositiveInt,
        original_path: Path,
    ) -> None:
        self.link_type = link_type
        self.link_id = link_id
        self.original_path = original_path

    def set_converted(self, converted_path: Path) -> None:
        self.temp_image_id = None
        self.converted_path = converted_path


@dataclass(slots=True, kw_only=True)
class NewImageEntity(ImageEntity):
    id: ImageId | None = None  # type: ignore[assignment]
