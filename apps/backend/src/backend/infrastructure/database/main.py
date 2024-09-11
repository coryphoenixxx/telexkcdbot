import logging

from sqlalchemy import URL, text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    create_async_engine,
)

from backend.infrastructure.database.config import DbConfig


def create_db_engine(config: DbConfig) -> AsyncEngine:
    db_url = URL.create(
        drivername=f"postgresql+{config.driver}",
        username=config.user,
        password=config.password,
        host=config.host,
        port=config.port,
        database=config.dbname,
    )

    return create_async_engine(
        url=db_url,
        echo=config.echo,
        echo_pool=config.echo,
        pool_size=config.pool_size,
        max_overflow=20,
    )


async def check_db_connection(engine: AsyncEngine) -> None:
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except ConnectionError as e:
        logging.fatal(f"Database connection failed! ERROR: {e.strerror}")
