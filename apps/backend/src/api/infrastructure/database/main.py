import logging

from sqlalchemy import URL, text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from api.infrastructure.database.config import DbConfig


def create_db_engine(config: DbConfig) -> AsyncEngine:
    return create_async_engine(
        url=URL.create(
            drivername=f"postgresql+{config.driver}",
            username=config.user,
            password=config.password,
            host=config.host,
            port=config.port,
            database=config.dbname,
        ),
        echo=config.echo,
        echo_pool=config.echo,
        pool_size=config.pool_size,
    )


def create_db_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(
        bind=engine,
        expire_on_commit=False,
        autoflush=False,
    )


async def check_db_connection(engine: AsyncEngine) -> None:
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except ConnectionError as e:
        logging.fatal(f"Database connection failed! ERROR: {e.strerror}")
