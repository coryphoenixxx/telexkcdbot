import logging
from types import TracebackType

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from api.infrastructure.database.config import DbConfig
from api.infrastructure.database.gateways import (
    ComicGateway,
    TranslationGateway,
    TranslationImageGateway,
)

__all__ = [
    "ComicGateway",
    "TranslationImageGateway",
    "TranslationGateway",
    "create_db_engine",
    "create_db_session_factory",
    "check_db_connection",
    "DbConfig",
    "UnitOfWork",
]


def create_db_engine(config: DbConfig) -> AsyncEngine:
    return create_async_engine(
        url=config.dsn,
        echo=config.echo,
        echo_pool=config.echo,
        pool_size=config.pool_size,
        pool_pre_ping=True,
    )


def create_db_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(
        bind=engine,
        expire_on_commit=True,
        autoflush=True,
    )


async def check_db_connection(engine: AsyncEngine):
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except ConnectionError as e:
        logging.fatal(f"Database connection failed! ERROR: {e.strerror}")


class UnitOfWork:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def __aenter__(self) -> "UnitOfWork":
        return self

    async def __aexit__(
            self,
            exc_type: type[BaseException] | None,
            exc_val: BaseException | None,
            exc_tb: TracebackType | None,
    ) -> None:
        if exc_type:
            await self.rollback()
        await self._session.close()

    async def commit(self) -> None:
        await self._session.commit()

    async def rollback(self) -> None:
        await self._session.rollback()
