from pathlib import Path

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.images.dtos import TranslationImageRequestDTO

from .models import TranslationImageModel
from .types import TranslationImageID


class TranslationImageRepo:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(
        self,
        image_dto: TranslationImageRequestDTO,
        image_save_path: Path,
    ) -> TranslationImageID:
        stmt = (
            insert(TranslationImageModel)
            .values(
                version=image_dto.version,
                path=str(image_save_path),
            )
            .returning(TranslationImageModel.id)
        )

        return (await self._session.execute(stmt)).scalar_one()
