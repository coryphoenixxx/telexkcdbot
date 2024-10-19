from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any

from backend.domain.value_objects import ImageId, PositiveInt, TempFileUUID
from backend.domain.value_objects.image_file import ImageFormat


class ImageLinkType(StrEnum):
    TRANSLATION = "TRANSLATION"
    USER = "USER"


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
    entity_type: ImageLinkType | None = None
    entity_id: PositiveInt | None = None
    image_path: Path | None = None
    meta: ImageMeta
    is_deleted: bool = False

    def has_another_owner(self, link_type: ImageLinkType, link_id: PositiveInt) -> bool:
        if self.entity_type and self.entity_id:
            return (self.entity_type, self.entity_id.value) != (link_type, link_id.value)
        return False

    def create(
        self,
        entity_type: ImageLinkType,
        entity_id: PositiveInt,
        original_path: Path,
    ) -> None:
        self.entity_type = entity_type
        self.entity_id = entity_id
        self.image_path = original_path


@dataclass(slots=True, kw_only=True)
class NewImageEntity(ImageEntity):
    id: ImageId | None = None  # type: ignore[assignment]
