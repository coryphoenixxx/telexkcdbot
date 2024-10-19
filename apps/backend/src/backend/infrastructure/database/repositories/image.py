from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert

from backend.application.image.exceptions import ImageNotFoundError
from backend.application.image.interfaces import ImageRepoInterface
from backend.domain.entities import ImageEntity, ImageLinkType, NewImageEntity
from backend.domain.value_objects import ImageId, PositiveInt
from backend.infrastructure.database.mappers import (
    map_image_entity_to_dict,
    map_image_model_to_entity,
)
from backend.infrastructure.database.models import ImageModel
from backend.infrastructure.database.repositories import BaseRepo


class ImageRepo(BaseRepo, ImageRepoInterface):
    async def create(self, image: NewImageEntity) -> ImageId:
        image_id: int = await self.session.scalar(  # type: ignore[assignment]
            insert(ImageModel)
            .values(map_image_entity_to_dict(image))
            .returning(ImageModel.image_id)
        )
        return ImageId(image_id)

    async def update(self, image: ImageEntity) -> None:
        await self.session.execute(
            update(ImageModel)
            .where(ImageModel.image_id == image.id.value)
            .values(map_image_entity_to_dict(image))
        )

    async def get_linked_image_id(
        self,
        link_type: ImageLinkType,
        link_id: PositiveInt,
    ) -> ImageId | None:
        image_id: int | None = await self.session.scalar(
            select(ImageModel.image_id).where(
                ImageModel.entity_id == link_id.value,
                ImageModel.entity_type == link_type,
                ImageModel.is_deleted.is_(False),
            )
        )

        return ImageId(image_id) if image_id else None

    async def load(self, image_id: ImageId) -> ImageEntity:
        image: ImageModel | None = await self.session.get(
            ImageModel,
            image_id.value,
            with_for_update=True,
        )

        if image is None:
            raise ImageNotFoundError(image_id)

        return map_image_model_to_entity(image)
