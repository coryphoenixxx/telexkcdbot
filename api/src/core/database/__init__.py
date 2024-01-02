import logging
from collections.abc import Generator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.core.config import DbConfig, settings


class Database:
    def __init__(self, config: DbConfig):
        self._config = config
        self._engine = self.create_engine(config)
        self._session_factory = self.create_session_factory(self._engine)

    @staticmethod
    def create_engine(config: DbConfig) -> AsyncEngine:
        return create_async_engine(
            url=config.pg.dsn,
            echo=config.sqla.echo,
            echo_pool=config.sqla.echo,
            pool_size=config.sqla.pool_size,
        )

    @staticmethod
    def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
        return async_sessionmaker(
            bind=engine,
            expire_on_commit=True,
            autoflush=True,
        )

    @property
    def engine(self) -> AsyncEngine:
        return self._engine

    def get_session_factory(self) -> Generator[async_sessionmaker, None, None]:
        yield self._session_factory

    async def connect(self):
        try:
            async with self._engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
        except ConnectionError as e:
            logging.fatal(f"Database connection failed! ERROR: {e.strerror}")

    async def disconnect(self):
        await self._engine.dispose()


db = Database(config=settings.db)
