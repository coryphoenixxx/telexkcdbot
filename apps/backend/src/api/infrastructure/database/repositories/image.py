from pathlib import Path

from shared.utils import cast_or_none
from sqlalchemy import update
from sqlalchemy.dialects.postgresql import insert

from api.application.dtos.responses import (
    TranslationImageOrphanResponseDTO,
    TranslationImageResponseDTO,
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

    async def attach_image(
        self,
        translation_id: TranslationID,
        image_id: TranslationImageID | None,
    ) -> None:
        if not image_id:
            return

        db_image = await self._get_model_by_id(TranslationImageModel, image_id)

        if not db_image:
            raise ImageNotFoundError(image_id)

        owner_id = db_image.translation_id
        if owner_id:
            raise ImageAlreadyAttachedError(
                image_id=TranslationImageID(db_image.image_id),
                translation_id=TranslationID(owner_id),
            )

        db_image.translation_id = translation_id

    async def get_by_id(self, image_id: TranslationImageID) -> TranslationImageResponseDTO | None:
        image = await self._get_model_by_id(TranslationImageModel, image_id)
        if image:
            return TranslationImageResponseDTO.from_model(image)
        return None
