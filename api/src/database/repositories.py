
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from src.database.base import SessionFactory
from src.database.models import Comic, Favorite


class ComicRepo:
    @classmethod
    async def get_by_id(
            cls,
            comic_id: int,
            fields: str | None = None,
    ):
        selected_columns = Comic.filter_columns(fields)

        async with SessionFactory() as session:
            stmt = select(*selected_columns) \
                .where(Comic.comic_id == comic_id)

            row = (await session.execute(stmt)).fetchone()

        return row

    @classmethod
    async def get_list(
            cls,
            fields: str | None = None,
            limit: int | None = None,
            offset: int | None = None,
            order: str | None = 'esc',
    ):
        selected_columns = Comic.filter_columns(fields)

        async with SessionFactory() as session:
            stmt = select(*selected_columns)

            if order == 'esc':
                stmt = stmt.order_by(Comic.comic_id)
            elif order == 'desc':
                stmt = stmt.order_by(Comic.comic_id.desc())
            if limit:
                stmt = stmt.limit(limit)
            if offset:
                stmt = stmt.offset(offset)

            rows = (await session.execute(stmt)).fetchall()
            total = (await session.execute(select(func.count('*')).select_from(Comic))).scalar()

        meta = {
            'meta': {
                'limit': limit,
                'offset': offset,
                'count': len(rows),
                'total': total,
            },
        }

        return rows, meta

    @classmethod
    async def search(
            cls,
            fields: str | None = None,
            limit: int | None = None,
            offset: int | None = None,
            q: str | None = None,
    ):
        selected_columns = Comic.filter_columns(fields)

        async with SessionFactory() as session:
            stmt = select(*selected_columns) \
                .where(Comic.search_vector_.match(q))

            if limit:
                stmt = stmt.limit(limit)
            if offset:
                stmt = stmt.offset(offset)

            rows = (await session.execute(stmt)).fetchall()
            total = (await session.execute(select(func.count('*')).select_from(Comic))).scalar()

        meta = {
            'meta': {
                'limit': limit,
                'offset': offset,
                'count': len(rows),
                'total': total,
            },
        }

        return rows, meta

    @classmethod
    async def add(
            cls,
            comic_data: list[dict] | dict,  # TODO:
    ):
        async with SessionFactory() as session:
            await session.execute(
                insert(Comic).returning(Comic.comic_id).on_conflict_do_nothing(),
                comic_data,
            )

    @classmethod
    async def get_favorites_count(
            cls,
            comic_id: int,
    ):
        async with SessionFactory() as session:
            stmt = select(func.count('*')) \
                .select_from(Favorite) \
                .where(Favorite.comic_id == comic_id)

            favorites_count = (await session.execute(stmt)).scalar()

        return favorites_count
