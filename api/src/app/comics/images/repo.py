from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from .dtos import TranslationImageDTO
from .models import TranslationImageModel
from .types import TranslationImageId


class TranslationImageRepo:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, image_dto: TranslationImageDTO, image_save_path: str) -> TranslationImageId:
        stmt = insert(TranslationImageModel).values(
            version=image_dto.version,
            path=image_save_path,
            dimensions=image_dto.image_obj.dimensions,
        ).returning(TranslationImageModel.id)

        return (await self._session.execute(stmt)).scalar_one()
