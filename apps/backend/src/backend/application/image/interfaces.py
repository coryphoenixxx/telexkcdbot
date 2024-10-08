from collections.abc import Iterable
from typing import Protocol

from backend.domain.entities import ImageEntity, ImageLinkType, NewImageEntity
from backend.domain.value_objects import ImageFileObj, ImageId, PositiveInt


class ImageConverterInterface(Protocol):
    def convert_to_webp(self, original: ImageFileObj) -> ImageFileObj: ...


class ImageRepoInterface(Protocol):
    async def create(self, new_image: NewImageEntity) -> ImageId: ...

    async def get_linked_image_ids(
        self,
        link_type: ImageLinkType,
        link_id: PositiveInt,
    ) -> Iterable[ImageId]: ...

    async def update(self, image: ImageEntity) -> None: ...

    async def load(self, image_id: ImageId) -> ImageEntity: ...
