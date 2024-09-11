from pathlib import Path

from sqlalchemy import and_, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import joinedload

from backend.application.dtos import TranslationImageRequestDTO, TranslationImageResponseDTO
from backend.core.value_objects import TranslationImageID
from backend.infrastructure.database.models import TranslationImageModel, TranslationModel
from backend.infrastructure.database.repositories.base import BaseRepo
from backend.infrastructure.utils import cast_or_none


class TranslationImageRepo(BaseRepo):
    async def create(self, dto: TranslationImageRequestDTO) -> TranslationImageResponseDTO:
        stmt = (
            insert(TranslationImageModel)
            .values(
                translation_id=None,
                original=str(dto.original),
                converted=cast_or_none(str, dto.converted),
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

        return TranslationImageResponseDTO.from_model(image)

    async def update_converted(
        self,
        image_id: TranslationImageID,
        converted_rel_path: Path | None,
    ) -> None:
        stmt = (
            update(TranslationImageModel)
            .where(and_(TranslationImageModel.image_id == image_id.value))
            .values(
                converted=cast_or_none(str, converted_rel_path),
            )
            .returning(TranslationImageModel.image_id)
        )

        await self._session.execute(stmt)

    async def get_by_id(self, image_id: TranslationImageID) -> TranslationImageResponseDTO | None:
        image = await self._get_model_by_id(TranslationImageModel, image_id.value)
        if image:
            return TranslationImageResponseDTO.from_model(image)
        return None
