import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from api.infrastructure.database.config import DBConfig
from api.infrastructure.database.repositories import (
    ComicRepo,
    TranslationImageRepo,
    TranslationRepo,
)

__all__ = [
    "ComicRepo",
    "TranslationImageRepo",
    "TranslationRepo",
    "create_db_engine",
    "create_db_session_factory",
    "check_db_connection",
    "DBConfig"
]


def create_db_engine(config: DBConfig) -> AsyncEngine:
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
