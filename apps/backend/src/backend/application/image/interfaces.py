from collections.abc import Iterable, Sequence
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

    async def update_many(self, images: Sequence[ImageEntity]) -> None: ...

    async def load(self, image_id: ImageId) -> ImageEntity: ...

    async def load_many(self, image_ids: Iterable[ImageId]) -> Sequence[ImageEntity]: ...
