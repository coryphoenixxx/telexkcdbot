from sqlalchemy import delete, select, update
from sqlalchemy.orm import selectinload
from src.database import dto, models
from src.utils.validators import PostComicSchema, PutComicJSONSchema


class ComicRepository:
    def __init__(self, session_factory):
        self._session = session_factory

    @staticmethod
    def _get_by_id_query(comic_id: int):
        return select(models.Comic) \
            .options(selectinload(models.Comic.translations)) \
            .where(models.Comic.comic_id == comic_id)

    async def get_by_id(self, comic_id: int) -> dto.Comic | None:
        async with self._session() as session:
            comic = (await session.scalars(self._get_by_id_query(comic_id))).one_or_none()

            return comic.to_dto() if comic else None

    async def get_list(
            self,
            limit: int | None,
            offset: int | None,
            order: str = 'esc',
    ) -> tuple[list[dto.Comic], int]:
        async with self._session() as session:
            stmt = select(models.Comic) \
                .options(selectinload(models.Comic.translations)) \
                .limit(limit) \
                .offset(offset)
            if order == 'desc':
                stmt = stmt.order_by(models.Comic.comic_id.desc())

            result = (await session.scalars(stmt)).unique().all()

            total = await session.scalar(models.Comic.total_count)

            return [comic.to_dto() for comic in result], total

    async def search(
            self,
            q: str,
            limit: int | None,
            offset: int | None,
    ) -> tuple[list[dto.Comic], int]:
        async with self._session() as session:
            stmt = select(models.Comic) \
                .join(models.Comic.translations) \
                .options(selectinload(models.Comic.translations)) \
                .where(models.ComicTranslation.search_vector.match(q)) \
                .limit(limit) \
                .offset(offset)

            comics = (await session.scalars(stmt)).unique().all()
            total = await session.scalar(models.Comic.total_count)

            return [comic.to_dto() for comic in comics], total

    async def create(self, comic_data: PostComicSchema) -> dto.Comic:
        async with self._session() as session:
            comic = models.Comic(
                comic_id=comic_data.comic_id,
                publication_date=comic_data.publication_date,
                is_specific=comic_data.is_specific,
                translations=[models.ComicTranslation(**tr.model_dump()) for tr in comic_data.translations],
            )

            session.add(comic)

            await session.commit()
            await session.refresh(comic)

            comic = (await session.scalars(self._get_by_id_query(comic.comic_id))).one()

            return comic.to_dto()

    async def update(self, comic_id: int, comic_data: PutComicJSONSchema) -> dto.Comic | None:
        async with self._session() as session:
            stmt = update(models.Comic).values(
                comic_id=comic_id,
                publication_date=comic_data.publication_date,
                is_specific=comic_data.is_specific,
            )
            await session.execute(stmt)

            translations = [{'comic_id': comic_id} | tr.model_dump() for tr in comic_data.translations]

            await session.execute(update(models.ComicTranslation), translations)
            await session.commit()

            comic = (await session.scalars(self._get_by_id_query(comic_id))).one()

            return comic.to_dto(translation=comic.translations)

    async def delete(self, comic_id: int) -> int:
        async with self._session() as session:
            stmt = delete(models.Comic) \
                .where(models.Comic.comic_id == comic_id) \
                .returning(models.Comic.comic_id)

            comic_id = await session.scalar(stmt)

            return comic_id
