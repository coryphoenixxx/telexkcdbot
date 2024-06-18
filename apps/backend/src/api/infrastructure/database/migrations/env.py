import asyncio

from alembic import context
from shared.config_loader import load_config
from sqlalchemy import Connection

from api.infrastructure.database.config import DbConfig
from api.infrastructure.database.main import create_db_engine
from api.infrastructure.database.models import BaseModel

config = context.config

target_metadata = BaseModel.metadata


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    engine = create_db_engine(config=load_config(DbConfig, scope="db"))

    async with engine.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await engine.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


run_migrations_online()
