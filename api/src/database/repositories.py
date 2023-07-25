from sqlalchemy import func, select, update
from sqlalchemy.dialects.postgresql import insert
from src.database.models import Comic, Favorite


class ComicRepository:
    def __init__(self, session_factory):
        self._session = session_factory

    async def get_by_id(self, comic_id: int) -> tuple[dict | None, int]:

        async with self._session() as session:
            stmt1 = select(Comic) \
                .where(Comic.comic_id == comic_id)

            stmt2 = select(func.count(Favorite.fav_id)) \
                .where(Favorite.comic_id == comic_id)

            comic = (await session.scalars(stmt1)).one_or_none()
            favorite_count = await session.scalar(stmt2)

            return comic.as_dict() if comic else None, favorite_count

    async def get_list(
            self,
            limit: int | None = None,
            offset: int | None = None,
            order: str | None = None,
    ) -> tuple[list[dict], int]:

        async with self._session() as session:
            stmt = select(Comic)

            stmt = stmt.order_by(Comic.comic_id.desc()) if order == 'desc' else stmt.order_by(Comic.comic_id)

            if limit:
                stmt = stmt.limit(limit)
            if offset:
                stmt = stmt.offset(offset)

            result = [comic.as_dict() for comic in (await session.scalars(stmt))]
            total = await session.scalar(select(func.count(Comic.comic_id)))

            return result, total

    async def search(
            self,
            q: str | None = None,
            limit: int | None = None,
            offset: int | None = None,
    ) -> tuple[list[dict], int]:

        async with self._session() as session:
            stmt = select(Comic) \
                .where(Comic.search_vector_.match(q))

            if limit:
                stmt = stmt.limit(limit)
            if offset:
                stmt = stmt.offset(offset)

            result = [comic.as_dict() for comic in (await session.scalars(stmt))]
            total = await session.scalar(select(func.count(Comic.comic_id)))

            return result, total

    async def add(self, comic_data: dict) -> dict:

        async with self._session() as session:
            stmt = insert(Comic).returning(Comic)

            return (await session.scalar(stmt, comic_data)).as_dict()

    async def update(self, comic_id: int, comic_data: dict) -> dict | None:

        async with self._session() as session:
            stmt = update(Comic) \
                .where(Comic.comic_id == comic_id) \
                .values(**comic_data) \
                .returning(Comic)

            comic = await session.scalar(stmt, comic_data)

            return comic.as_dict() if comic else None
