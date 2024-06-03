from pathlib import Path

from shared.utils import cast_or_none
from sqlalchemy import update
from sqlalchemy.dialects.postgresql import insert

from api.application.dtos.responses.image import TranslationImageOrphanResponseDTO
from api.infrastructure.database.gateways.base import BaseGateway
from api.infrastructure.database.models.translation import TranslationImageModel
from api.my_types import TranslationImageID


class TranslationImageGateway(BaseGateway):
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
