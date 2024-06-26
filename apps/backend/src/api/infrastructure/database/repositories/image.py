from pathlib import Path

from shared.utils import cast_or_none
from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert

from api.application.dtos.responses import (
    TranslationImageOrphanResponseDTO,
)
from api.core.exceptions import ImageAlreadyAttachedError, ImageNotFoundError
from api.core.value_objects import TranslationID, TranslationImageID
from api.infrastructure.database.models import TranslationImageModel
from api.infrastructure.database.repositories.base import BaseRepo


class TranslationImageRepo(BaseRepo):
    async def create(self, original_rel_path: Path) -> TranslationImageOrphanResponseDTO:
        stmt = (
            insert(TranslationImageModel)
            .values(original_rel_path=str(original_rel_path))
            .returning(
                TranslationImageModel.image_id,
                TranslationImageModel.original_rel_path,
            )
        )

        image_id, original_rel_path = (await self._session.execute(stmt)).one()

        return TranslationImageOrphanResponseDTO(
            id=image_id,
            original_rel_path=original_rel_path,
        )

    async def update(
        self,
        image_id: TranslationImageID,
        converted_rel_path: Path | None,
        thumbnail_rel_path: Path,
    ) -> TranslationImageID:
        stmt = (
            update(TranslationImageModel)
            .where(TranslationImageModel.image_id == image_id)
            .values(
                converted_rel_path=cast_or_none(str, converted_rel_path),
                thumbnail_rel_path=str(thumbnail_rel_path),
            )
            .returning(TranslationImageModel.image_id)
        )

        # TODO: handle case when image not exists

        image_id: int = (await self._session.execute(stmt)).scalar_one()

        return TranslationImageID(image_id)

    async def link(
        self,
        translation_id: TranslationID,
        image_ids: list[TranslationImageID],
    ) -> None:
        if not image_ids:
            return

        image_ids = sorted(set(image_ids))

        db_images = (
            await self._session.scalars(
                select(TranslationImageModel)
                .where(
                    TranslationImageModel.image_id.in_(image_ids),
                )
                .order_by(TranslationImageModel.image_id)
            )
        ).all()

        db_image_ids = {image.image_id for image in db_images}
        for img_id in image_ids:
            if img_id not in db_image_ids:
                raise ImageNotFoundError(img_id)

        for img in db_images:
            owner_id = img.translation_id
            if owner_id and owner_id != translation_id:
                raise ImageAlreadyAttachedError(img.image_id, owner_id)

        for img in db_images:
            img.translation_id = translation_id
