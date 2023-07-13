from sqlalchemy import and_, func, select
from sqlalchemy.dialects.postgresql import insert
from src.database.base import SessionFactory
from src.database.models import Bookmark, Comic


class ComicDb:
    @staticmethod
    def _get_select_columns(fields):
        select_columns = Comic.filter_columns(fields)

        if not fields or 'bookmarked_count' in fields:
            select_columns.append(func.count(Bookmark.comic_id).label('bookmarked_count'))
        return select_columns

    @staticmethod
    async def _get_total(session):
        return (await session.execute(select(func.count('*')).select_from(Comic))).scalar()

    @classmethod
    async def get_comic_detail(
            cls,
            comic_id: int,
            fields: str | None = None,
            user_id: int | None = None,
    ):
        select_columns = cls._get_select_columns(fields)

        if user_id:
            subquery = select(func.count('*') > 0) \
                .select_from(Bookmark) \
                .where(and_(Bookmark.user_id == user_id, Bookmark.comic_id == comic_id)) \
                .scalar_subquery() \
                .label('is_bookmarked_by_user')
            select_columns.append(subquery)

        async with SessionFactory() as session:
            stmt = select(*select_columns) \
                .outerjoin(Bookmark) \
                .where(Comic.comic_id == comic_id) \
                .group_by(Comic)

            row = (await session.execute(stmt)).fetchone()

        return row

    @classmethod
    async def get_comic_list(
            cls,
            fields: str | None = None,
            limit: int | None = None,
            offset: int | None = None,
            order: str | None = None,
    ):
        select_columns = cls._get_select_columns(fields)

        async with SessionFactory() as session:
            stmt = select(*select_columns) \
                .outerjoin(Bookmark) \
                .group_by(Comic)

            if order == 'esc':
                stmt = stmt.order_by(Comic.comic_id)
            elif order == 'desc':
                stmt = stmt.order_by(Comic.comic_id.desc())
            if limit:
                stmt = stmt.limit(limit)
            if offset:
                stmt = stmt.offset(offset)

            rows = (await session.execute(stmt)).fetchall()
            total = await cls._get_total(session)

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
    async def get_found_comic_list(
            cls,
            fields: str | None = None,
            limit: int | None = None,
            offset: int | None = None,
            q: str | None = None,
    ):
        select_columns = cls._get_select_columns(fields)

        async with SessionFactory() as session:
            stmt = select(*select_columns) \
                .outerjoin(Bookmark) \
                .where(Comic._ts_vector.bool_op("@@")(func.to_tsquery(q))) \
                .group_by(Comic) \
                .order_by(func.ts_rank(Comic._ts_vector, func.to_tsquery(q)).desc())

            if limit:
                stmt = stmt.limit(limit)
            if offset:
                stmt = stmt.offset(offset)

            rows = (await session.execute(stmt)).fetchall()
            total = await cls._get_total(session)

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
    async def add_comics(cls, comic_data_list: list[dict]):
        async with SessionFactory() as session:
            await session.execute(
                insert(Comic).returning(Comic.comic_id).on_conflict_do_nothing(),
                comic_data_list,
            )
