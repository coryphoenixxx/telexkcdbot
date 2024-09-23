from pathlib import Path

from sqlalchemy import and_, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import joinedload

from backend.application.comic.dtos import TranslationImageRequestDTO, TranslationImageResponseDTO
from backend.application.comic.interfaces import TranslationImageRepoInterface
from backend.application.utils import cast_or_none
from backend.core.value_objects import TranslationImageID
from backend.infrastructure.database.models import TranslationImageModel, TranslationModel
from backend.infrastructure.database.repositories import BaseRepo


class TranslationImageRepo(BaseRepo, TranslationImageRepoInterface):
    async def create(self, dto: TranslationImageRequestDTO) -> TranslationImageResponseDTO:
        stmt = (
            insert(TranslationImageModel)
            .values(
                translation_id=None,
                original=str(dto.original_path),
                converted=cast_or_none(str, dto.converted_path),
            )
            .returning(TranslationImageModel)
        )

        image = (await self._session.execute(stmt)).scalar_one()

        translation = await self._get_model_by_id(
            TranslationModel,
            dto.translation_id.value,
            options=joinedload(TranslationModel.image),
        )
        if translation:
            translation.image = image  # TODO: Also unattached old image if exists

        await self._session.flush()

        return image.to_dto()

    async def set_converted_path(
        self,
        translation_image_id: TranslationImageID,
        converted_rel_path: Path,
    ) -> None:
        stmt = (
            update(TranslationImageModel)
            .where(and_(TranslationImageModel.image_id == translation_image_id.value))
            .values(
                converted=str(converted_rel_path),
            )
            .returning(TranslationImageModel.image_id)
        )

        await self._session.execute(stmt)

    async def get_by_id(self, image_id: TranslationImageID) -> TranslationImageResponseDTO | None:
        if image := await self._get_model_by_id(TranslationImageModel, image_id.value):
            return image.to_dto()
        return None
