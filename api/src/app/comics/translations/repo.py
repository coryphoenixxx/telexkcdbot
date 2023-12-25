from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from .dtos import TranslationCreateDTO
from .models import TranslationModel


class TranslationRepo:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def add_to_comic(
        self,
        comic_id,
        translation_dto: TranslationCreateDTO,
    ) -> TranslationModel:

        stmt = (
            insert(TranslationModel).values(
                comic_id=comic_id,
                title=translation_dto.title,
                tooltip=translation_dto.tooltip,
                transcript=translation_dto.transcript,
                news_block=translation_dto.news_block,
                images=translation_dto.images,
                language=translation_dto.language,
                is_draft=translation_dto.is_draft,
            ).returning(TranslationModel)
        )
        result = (await self._session.scalars(stmt)).one()
        return result
