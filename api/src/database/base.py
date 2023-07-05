from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from src.api_config import DATABASE_URL
from src.database.models import Base


class BaseDB:
    pool: async_sessionmaker

    @classmethod
    async def init(cls):
        engine = create_async_engine(DATABASE_URL, echo=False, echo_pool=True, pool_size=20)
        cls.pool = async_sessionmaker(engine, expire_on_commit=True)

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        await engine.dispose()


class SessionFactory:
    _db = BaseDB

    async def __aenter__(self):
        self._session = self._db.pool()
        await self._session.begin()
        return self._session

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            await self._session.rollback()
        await self._session.commit()
