
from sqlalchemy import delete, select, update
from sqlalchemy.dialects.postgresql import insert
from src.database import dto, models


class ComicRepository:
    def __init__(self, session_factory):
        self._session = session_factory

    async def get_by_id(self, comic_id: int) -> dto.Comic | None:

        async with self._session() as session:
            stmt = select(models.Comic) \
                .where(models.Comic.comic_id == comic_id)

            comic = (await session.scalars(stmt)).one_or_none()

            return comic.to_dto() if comic else None

    async def get_list(
            self,
            limit: int | None,
            offset: int | None,
            order: str = 'esc',
    ) -> tuple[list[dto.Comic], int]:

        async with self._session() as session:
            stmt = select(models.Comic) \
                .limit(limit) \
                .offset(offset)
            if order == 'desc':
                stmt = stmt.order_by(models.Comic.comic_id.desc())

            comics = (await session.scalars(stmt)).all()
            total = await session.scalar(models.Comic.total_count)

            return [comic.to_dto() for comic in comics], total

    async def search(
            self,
            q: str,
            limit: int | None,
            offset: int | None,
    ) -> tuple[list[dto.Comic], int]:

        async with self._session() as session:
            stmt = select(models.Comic) \
                .limit(limit) \
                .offset(offset) \
                .where(models.Comic.search_vector.match(q))

            comics = (await session.scalars(stmt)).all()
            total = await session.scalar(models.Comic.total_count)

            return [comic.to_dto() for comic in comics], total

    async def add(self, comic_data: dict) -> dto.Comic:

        async with self._session() as session:
            stmt = insert(models.Comic) \
                .values(**comic_data) \
                .returning(models.Comic.comic_id)
            comic_id = await session.scalar(stmt)

            comic = (await session.scalars(
                select(models.Comic).where(models.Comic.comic_id == comic_id),
            )).one()

            return comic.to_dto()

    async def update(self, comic_id: int, comic_data: dict) -> dto.Comic | None:

        async with self._session() as session:
            stmt = update(models.Comic) \
                .where(models.Comic.comic_id == comic_id) \
                .values(**comic_data) \
                .returning(models.Comic.comic_id)

            comic_id = await session.scalar(stmt)

            if comic_id:
                comic = (await session.scalars(
                    select(models.Comic).where(models.Comic.comic_id == comic_id),
                )).one()
                return comic.to_dto()
            return None

    async def delete(self, comic_id: int) -> int:

        async with self._session() as session:
            stmt = delete(models.Comic) \
                .where(models.Comic.comic_id == comic_id) \
                .returning(models.Comic.comic_id)

            comic_id = await session.scalar(stmt)

            return comic_id
