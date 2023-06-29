from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.api_config import DATABASE_URL
from src.databases.models import Comic, Bookmark, Base


class BaseDB:
    engine = create_async_engine(DATABASE_URL, future=True, echo=True)
    pool = async_sessionmaker(engine, expire_on_commit=False)

    @classmethod
    async def init(cls):
        async with cls.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        await cls.engine.dispose()


class SessionFactory:
    _db = BaseDB

    def __init__(self):
        _session = None

    async def __aenter__(self):
        self._session = self._db.pool()
        await self._session.begin()
        return self._session

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._session.commit()


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
                .where(and_(Bookmark.user_id == int(user_id), Bookmark.comic_id == int(comic_id))) \
                .scalar_subquery() \
                .label('bookmarked_by_user')
            select_columns.append(subquery)

        async with SessionFactory() as session:
            stmt = select(*select_columns) \
                .select_from(Comic, Bookmark) \
                .outerjoin(Bookmark) \
                .where(Comic.comic_id == int(comic_id)) \
                .group_by(Comic.comic_id)

            row = (await session.execute(stmt)).fetchone()

        return row

    @classmethod
    async def get_comic_list(cls, valid_query_params):
        fields, limit, offset, q = (valid_query_params.get(param) for param in ('fields', 'limit', 'offset', 'q'))

        select_columns = Comic.get_columns(fields)

        if not fields or 'bookmarked_count' in fields:
            select_columns.append(func.count(Bookmark.comic_id).label('bookmarked_count'))

        async with SessionFactory() as session:
            stmt = select(*select_columns) \
                .outerjoin(Bookmark)

            if q:
                stmt = stmt.where(Comic._ts_vector.bool_op("@@")(func.to_tsquery(q)))

            stmt = stmt.group_by(Comic.comic_id) \
                .order_by(Comic.comic_id)

            if limit:
                stmt = stmt.limit(limit)

            if offset:
                stmt = stmt.offset(offset)

            rows = (await session.execute(stmt)).fetchall()

        return rows


class UserDB(BaseDB):
    ...
