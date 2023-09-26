from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from src import dtos
from src.database import models


class ComicRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, comic_dto: dtos.ComicOriginRequestDTO) -> models.Comic:
        async with self._session, self._session.begin():
            translation = models.ComicTranslation(**comic_dto.text_data.to_dict())
            comic_model = models.Comic(
                **comic_dto.to_dict(),
                translations=[translation],
            )

            self._session.add(comic_model)

            comic_model = (await self._session.scalars(self._get_by_id_stmt(comic_model.comic_id))).one()

            await self._session.commit()

        return comic_model

    async def get_by_id(self, comic_id: int) -> models.Comic | None:
        async with self._session:
            comic_model: models.Comic = (await self._session.scalars(self._get_by_id_stmt(comic_id))).one_or_none()
            return comic_model

    async def update_translation_image(self, comic_id: int, lang: str, new_image: str):
        async with self._session, self._session.begin():
            stmt = update(models.ComicTranslation). \
                where(models.ComicTranslation.comic_id == comic_id). \
                where(models.ComicTranslation.language_code == lang). \
                values(image_url=new_image)

            await self._session.execute(stmt)
            await self._session.commit()

    @staticmethod
    def _get_by_id_stmt(comic_id: int):
        return select(models.Comic) \
            .options(selectinload(models.Comic.translations)) \
            .where(models.Comic.comic_id == comic_id)
