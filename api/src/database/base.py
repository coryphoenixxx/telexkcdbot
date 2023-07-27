from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from src.config import DbConfig


class SessionFactory:
    pool: async_sessionmaker

    @classmethod
    def configure(cls, db_config: DbConfig):
        engine = create_async_engine(
            db_config.postgres_dsn,
            echo=db_config.sqla_echo,
            echo_pool=db_config.sqla_echo,
            pool_size=db_config.pool_size,
        )
        cls.pool = async_sessionmaker(bind=engine, expire_on_commit=True)
        return cls

    async def __aenter__(self):
        self._session = self.pool()
        return self._session

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            await self._session.rollback()
        await self._session.commit()
