from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine


class SessionFactory:
    pool: async_sessionmaker

    @classmethod
    def configure(cls, db_url):
        engine = create_async_engine(db_url, echo=True, echo_pool=True, pool_size=20)
        cls.pool = async_sessionmaker(bind=engine, expire_on_commit=True)

    async def __aenter__(self):
        self._session = self.pool()
        await self._session.begin()
        return self._session

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            await self._session.rollback()
        await self._session.commit()
