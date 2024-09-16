from typing import Any

from sqlalchemy import URL, text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from backend.infrastructure.database.config import DbConfig


def build_postgres_url(config: DbConfig) -> URL:
    return URL.create(
        drivername="postgresql+asyncpg",
        username=config.user,
        password=config.password,
        host=config.host,
        port=config.port,
        database=config.dbname,
    )


def create_db_engine(db_url: URL, **kwargs: Any) -> AsyncEngine:
    return create_async_engine(url=db_url, **kwargs)


async def check_db_connection(engine: AsyncEngine) -> None:
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))
