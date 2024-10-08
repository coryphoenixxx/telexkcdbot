from collections.abc import Iterable

from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert

from backend.application.image.exceptions import ImageNotFoundError
from backend.application.image.interfaces import ImageRepoInterface
from backend.domain.entities import ImageEntity, ImageLinkType, NewImageEntity
from backend.domain.utils import cast_or_none
from backend.domain.value_objects import ImageId, PositiveInt
from backend.infrastructure.database.mappers import map_image_model_to_entity
from backend.infrastructure.database.models import ImageModel
from backend.infrastructure.database.repositories import BaseRepo


class ImageRepo(BaseRepo, ImageRepoInterface):
    async def create(self, image: NewImageEntity) -> ImageId:
        image_id: int = await self.session.scalar(  # type: ignore[assignment]
            insert(ImageModel)
            .values(
                temp_image_id=image.temp_image_id.value if image.temp_image_id else None,
                link_type=image.link_type,
                link_id=image.link_id.value if image.link_id else None,
                original_path=cast_or_none(str, image.original_path),
                converted_path=cast_or_none(str, image.converted_path),
                converted_2x_path=cast_or_none(str, image.converted_2x_path),
                is_deleted=image.is_deleted,
            )
            .returning(ImageModel.image_id)
        )
        return ImageId(image_id)

    async def update(self, image: ImageEntity) -> None:
        await self.session.execute(
            update(ImageModel)
            .where(ImageModel.image_id == image.id.value)
            .values(
                temp_image_id=image.temp_image_id.value if image.temp_image_id else None,
                link_type=image.link_type,
                link_id=image.link_id.value if image.link_id else None,
                original_path=cast_or_none(str, image.original_path),
                converted_path=cast_or_none(str, image.converted_path),
                converted_2x_path=cast_or_none(str, image.converted_2x_path),
                is_deleted=image.is_deleted,
            )
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
            )
        )

        return [ImageId(image_id) for image_id in images_ids]

    async def load(self, image_id: ImageId) -> ImageEntity:
        image: ImageModel | None = await self.session.get(ImageModel, image_id.value)

        if image is None:
            raise ImageNotFoundError(image_id)

        return map_image_model_to_entity(image)
