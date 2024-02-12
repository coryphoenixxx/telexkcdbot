from pathlib import Path

from shared.utils import cast_or_none
from sqlalchemy import update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from api.application.dtos.responses.image import TranslationImageResponseDTO
from api.application.types import TranslationImageID
from api.infrastructure.database.models.translation import TranslationImageModel


class TranslationImageRepo:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, original_rel_path: Path) -> TranslationImageResponseDTO:
        stmt = (
            insert(TranslationImageModel)
            .values(original_rel_path=str(original_rel_path))
            .returning(
                TranslationImageModel.id,
                TranslationImageModel.original_rel_path,
            )
        )

        image_id, original_rel_path = (await self._session.execute(stmt)).one()

        return TranslationImageResponseDTO(
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
            .where(TranslationImageModel.id == image_id)
            .values(
                converted_rel_path=cast_or_none(str, converted_rel_path),
                thumbnail_rel_path=str(thumbnail_rel_path),
            )
            .returning(TranslationImageModel.id)
        )

        # handle case when image not exists

        image_id: int = (await self._session.execute(stmt)).scalar_one()

        return TranslationImageID(image_id)
