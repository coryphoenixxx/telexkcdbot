from typing import Protocol

from backend.domain.entities import ImageEntity, ImageLinkType, NewImageEntity
from backend.domain.entities.image import ImageMeta
from backend.domain.value_objects import ImageFileObj, ImageId, PositiveInt


class ImageFileProcessorInterface(Protocol):
    def convert_to_webp(self, original: ImageFileObj) -> ImageFileObj: ...


class ImageRepoInterface(Protocol):
    async def create(self, new_image: NewImageEntity) -> ImageId: ...

    async def get_linked_image_id(
        self,
        link_type: ImageLinkType,
        link_id: PositiveInt,
    ) -> ImageId | None: ...

    async def update(self, image: ImageEntity) -> None: ...

    async def get_metadata_by_id(self, image_id: ImageId) -> ImageMeta: ...

    async def load(self, image_id: ImageId) -> ImageEntity: ...
