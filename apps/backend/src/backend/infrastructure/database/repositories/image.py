from collections.abc import Iterable, Sequence

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

    async def update_many(self, images: Sequence[ImageEntity]) -> None:
        await self.session.execute(
            update(ImageModel),
            [map_image_entity_to_dict(image, with_id=True) for image in images],
        )

    async def get_linked_image_ids(
        self,
        link_type: ImageLinkType,
        link_id: PositiveInt,
    ) -> Iterable[ImageId]:
        images_ids: Iterable[int] = await self.session.scalars(
            select(ImageModel.image_id).where(
                ImageModel.link_id == link_id.value,
                ImageModel.link_type == link_type,
                ImageModel.is_deleted.is_(False),
            )
        )

        return [ImageId(image_id) for image_id in images_ids]

    async def load(self, image_id: ImageId) -> ImageEntity:
        image: ImageModel | None = await self.session.get(
            ImageModel,
            image_id.value,
            with_for_update=True,
        )

        if image is None:
            raise ImageNotFoundError(image_id)

        return map_image_model_to_entity(image)

    async def load_many(self, image_ids: Iterable[ImageId]) -> Sequence[ImageEntity]:
        stmt = select(ImageModel).where(
            ImageModel.image_id.in_(image_id.value for image_id in image_ids)
        )

        images: Sequence[ImageModel] = (await self.session.scalars(stmt)).all()

        return [map_image_model_to_entity(image) for image in images]
