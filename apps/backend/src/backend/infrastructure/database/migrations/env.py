import asyncio

import sqlalchemy
from alembic import context

from backend.infrastructure.config_loader import load_config
from backend.infrastructure.database.config import DbConfig
from backend.infrastructure.database.main import build_postgres_url, create_db_engine
from backend.infrastructure.database.models import BaseModel

config = context.config

target_metadata = BaseModel.metadata


def do_run_migrations(connection: sqlalchemy.Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    sqlalchemy_url = config.get_main_option("sqlalchemy.url")

    if sqlalchemy_url is not None:
        postgres_url = sqlalchemy.make_url(sqlalchemy_url)
    else:
        postgres_url = build_postgres_url(config=load_config(DbConfig, scope="db"))

    engine = create_db_engine(db_url=postgres_url)

    async with engine.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await engine.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


run_migrations_online()
