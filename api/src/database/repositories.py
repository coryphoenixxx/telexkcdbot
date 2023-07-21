from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from src.database.models import Comic, Favorite


class ComicRepository:
    def __init__(self, session_factory):
        self._session = session_factory

    async def get_by_id(self, comic_id: int) -> dict | None:
        async with self._session() as session:
            stmt = select(Comic) \
                .where(Comic.comic_id == comic_id)

            comic = (await session.scalars(stmt)).one_or_none()
            result = comic.as_dict()
        return result

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
            total = (await session.scalar(select(func.count(Comic.comic_id))))

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
            total = (await session.scalar(select(func.count(Comic.comic_id))))

        return result, total

    async def get_favorite_count(
            self,
            comic_id: int,
    ):
        async with self._session() as session:
            stmt = select(func.count(Favorite.fav_id)) \
                .where(Favorite.comic_id == comic_id)

            favorites_count = (await session.scalar(stmt))

        return favorites_count

    async def add(
            self,
            comic_data: list[dict] | dict,
    ):
        async with self._session() as session:
            comic_id = await session.scalar(
                insert(Comic).returning(Comic.comic_id),
                comic_data,
            )
        return comic_id
