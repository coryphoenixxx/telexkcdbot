from pathlib import Path

from sqlalchemy import update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import joinedload

from backend.application.dtos import (
    TranslationImageResponseDTO,
)
from backend.application.dtos.requests import TranslationImageRequestDTO
from backend.core.value_objects import TranslationID, TranslationImageID
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
            TranslationModel, dto.translation_id, options=(joinedload(TranslationModel.image),)
        )
        translation.image = image  # Also unattached old image if exists

        await self._session.flush()

        return TranslationImageResponseDTO(
            id=TranslationImageID(image.image_id),
            translation_id=TranslationID(image.translation_id),
            original=Path(image.original),
            converted=cast_or_none(Path, image.converted),
        )

    async def update_converted(
        self,
        image_id: TranslationImageID,
        converted_rel_path: Path | None,
    ) -> None:
        stmt = (
            update(TranslationImageModel)
            .where(TranslationImageModel.image_id == image_id)
            .values(
                converted=cast_or_none(str, converted_rel_path),
            )
            .returning(TranslationImageModel.image_id)
        )

        await self._session.execute(stmt)

    async def get_by_id(self, image_id: TranslationImageID) -> TranslationImageResponseDTO | None:
        image = await self._get_model_by_id(TranslationImageModel, image_id)
        if image:
            return TranslationImageResponseDTO.from_model(image)
        return None
