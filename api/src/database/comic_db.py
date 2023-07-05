from sqlalchemy import and_, func, select
from sqlalchemy.dialects.postgresql import insert
from src.database.base import SessionFactory
from src.database.models import Bookmark, Comic


class ComicDB:
    @staticmethod
    def get_select_columns(fields):
        select_columns = Comic.get_columns(fields)

        if not fields or 'bookmarked_count' in fields:
            select_columns.append(func.count(Bookmark.comic_id).label('bookmarked_count'))
        return select_columns

    @classmethod
    async def get_comic_detail(
            cls,
            comic_id: int,
            fields: str | None = None,
            user_id: int | None = None,
            **kwargs,
    ):
        select_columns = cls.get_select_columns(fields)

        if user_id:
            subquery = select(func.count('*') > 0) \
                .select_from(Bookmark) \
                .where(and_(Bookmark.user_id == user_id, Bookmark.comic_id == comic_id)) \
                .scalar_subquery() \
                .label('bookmarked_by_user')
            select_columns.append(subquery)

        async with SessionFactory() as session:
            stmt = select(*select_columns) \
                .select_from(Comic, Bookmark) \
                .outerjoin(Bookmark) \
                .where(Comic.comic_id == comic_id) \
                .group_by(Comic.comic_id)

            row = (await session.execute(stmt)).fetchone()

        return row

    @classmethod
    async def get_comic_list(
            cls,
            fields: str | None = None,
            limit: int | None = None,
            offset: int | None = None,
            order: str | None = None,
            **kwargs,
    ):
        select_columns = cls.get_select_columns(fields)

        async with SessionFactory() as session:
            stmt = select(*select_columns) \
                .outerjoin(Bookmark)

            stmt = stmt.group_by(Comic.comic_id)

            if not order or order == 'esc':
                stmt = stmt.order_by(Comic.comic_id)
            elif order == 'desc':
                stmt = stmt.order_by(Comic.comic_id.desc())

            if limit:
                stmt = stmt.limit(limit)
            if offset:
                stmt = stmt.offset(offset)

            rows = (await session.execute(stmt)).fetchall()

        meta = {
            'meta': {
                'limit': limit,
                'offset': offset,
                'total': len(rows),
            },
        }

        return rows, meta

    @classmethod
    async def get_found_comic_list(
            cls,
            fields: str | None = None,
            limit: int | None = None,
            offset: int | None = None,
            q: str | None = None,
            **kwargs,
    ):
        select_columns = cls.get_select_columns(fields)

        async with SessionFactory() as session:
            stmt = select(*select_columns) \
                .outerjoin(Bookmark) \
                .where(Comic._ts_vector.bool_op("@@")(func.to_tsquery(q))) \
                .group_by(Comic.comic_id) \
                .order_by(func.ts_rank(Comic._ts_vector, func.to_tsquery(q)).desc())

            if limit:
                stmt = stmt.limit(limit)
            if offset:
                stmt = stmt.offset(offset)

            rows = (await session.execute(stmt)).fetchall()

        meta = {
            'meta': {
                'limit': limit,
                'offset': offset,
                'total': len(rows),
            },
        }

        return rows, meta

    @classmethod
    async def add_comics(cls, comic_data_list: list[dict]):
        async with SessionFactory() as session:
            await session.execute(
                insert(Comic).returning(Comic.comic_id).on_conflict_do_nothing(),
                comic_data_list,
            )
