from sqlalchemy import func, select, and_
from sqlalchemy.dialects.postgresql import insert

from src.database.base import BaseDB, SessionFactory
from src.database.models import Comic, Bookmark


class ComicDB(BaseDB):
    @classmethod
    async def get_comic_detail(cls, comic_id, valid_query_params):
        fields = valid_query_params.get('fields')
        user_id = valid_query_params.get('user_id')

        select_columns = Comic.get_columns(fields)

        if not fields or 'bookmarked_count' in fields:
            select_columns.append(func.count(Bookmark.comic_id).label('bookmarked_count'))

        if user_id:
            subquery = select((func.count('*') > 0)) \
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
    async def get_comic_list(cls, valid_query_params):
        fields, limit, offset, order = (
            valid_query_params.get(param) for param in ('fields', 'limit', 'offset', 'order')
        )

        select_columns = Comic.get_columns(fields)

        if not fields or 'bookmarked_count' in fields:
            select_columns.append(func.count(Bookmark.comic_id).label('bookmarked_count'))

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
                'total': len(rows)
            }
        }

        return rows, meta

    @classmethod
    async def get_found_comic_list(cls, valid_query_params):
        fields, limit, offset, q = (valid_query_params.get(param) for param in ('fields', 'limit', 'offset', 'q'))

        select_columns = Comic.get_columns(fields)

        if not fields or 'bookmarked_count' in fields:
            select_columns.append(func.count(Bookmark.comic_id).label('bookmarked_count'))

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
                'total': len(rows)
            }
        }

        return rows, meta

    @classmethod
    async def add_comics(cls, comic_data_list):
        async with SessionFactory() as session:
            await session.execute(
                insert(Comic).on_conflict_do_nothing(),
                comic_data_list
            )
