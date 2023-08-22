from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import selectinload

from src import dtos
from src.database import models


class ComicsRepo:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self._session_factory = session_factory

    @staticmethod
    def _get_by_id_stmt(comic_id: int):
        return select(models.Comic) \
            .options(selectinload(models.Comic.translations)) \
            .where(models.Comic.comic_id == comic_id)

    async def get_by_id(self, comic_id: int) -> models.Comic | None:
        async with self._session_factory() as session:
            comic: models.Comic = (await session.scalars(self._get_by_id_stmt(comic_id))).one_or_none()
            return comic

    # async def get_list(
    #         self,
    #         limit: int | None,
    #         offset: int | None,
    #         order: types.OrderType,
    # ) -> tuple[list[types.ComicDTO], int]:
    #     async with self._session_factory() as session, session.begin():
    #         stmt = select(models.Comic) \
    #             .options(selectinload(models.Comic.translations)) \
    #             .limit(limit) \
    #             .offset(offset)
    #         if order == 'desc':
    #             stmt = stmt.order_by(models.Comic.comic_id.desc())
    #
    #         result = (await session.scalars(stmt)).unique().all()
    #
    #         total = await session.scalar(models.Comic.total_count)
    #
    #         return [comic.to_dto() for comic in result], total
    #
    # async def search(
    #         self,
    #         q: str,
    #         limit: int | None,
    #         offset: int | None,
    # ) -> tuple[list[types.ComicDTO], int]:
    #     async with self._session_factory() as session, session.begin():
    #         stmt = select(models.Comic) \
    #             .join(models.Comic.translations) \
    #             .options(selectinload(models.Comic.translations)) \
    #             .where(models.ComicTranslation.search_vector.match(q)) \
    #             .limit(limit) \
    #             .offset(offset)
    #
    #         comics = (await session.scalars(stmt)).unique().all()
    #         total = await session.scalar(models.Comic.total_count)
    #
    #         return [comic.to_dto() for comic in comics], total
    #
    async def create(self, comic_dto: dtos.ComicRequest) -> models.Comic:
        async with self._session_factory() as session, session.begin():
            translations = []

            for lang_code, tr_content in comic_dto.translations.items():
                translations.append(
                    models.ComicTranslation(
                        comic_id=comic_dto.comic_id,
                        language_code=lang_code,
                        **tr_content.to_dict(),
                    ),
                )

            comic = models.Comic(
                **comic_dto.to_dict(exclude=('translations',)),
                translations=translations,
            )

            session.add(comic)

            comic = (await session.scalars(self._get_by_id_stmt(comic.comic_id))).one()

        return comic
    #
    # async def update(self, comic_id: int, new_comic_data: types.PutComic) -> types.ComicDTO | None:
    #     async with self._session_factory() as session, session.begin():
    #         translations = [{'comic_id': comic_id} | tr.model_dump() for tr in new_comic_data.translations]
    #
    #         await session.execute(update(models.ComicTranslation), translations)
    #
    #         stmt = update(models.Comic).values(
    #             comic_id=comic_id,
    #             **new_comic_data.model_dump(exclude={'translations'}),
    #         )
    #
    #         await session.execute(stmt)
    #
    #         comic = (await session.scalars(self._get_by_id_stmt(comic_id))).one()
    #
    #         return comic.to_dto()
    #
    # async def delete(self, comic_id: int) -> int:
    #     async with self._session_factory() as session, session.begin():
    #         stmt = delete(models.Comic) \
    #             .where(models.Comic.comic_id == comic_id) \
    #             .returning(models.Comic.comic_id)
    #
    #         comic_id = await session.scalar(stmt)
    #
    #         return comic_id
