from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from .dtos import TranslationCreateDTO
from .models import TranslationModel


class TranslationRepo:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def add(self, translation_dto: TranslationCreateDTO) -> TranslationModel:
        stmt = (
            insert(TranslationModel).values(translation_dto.to_dict()).returning(TranslationModel)
        )
        result = (await self._session.scalars(stmt)).one()
        return result
