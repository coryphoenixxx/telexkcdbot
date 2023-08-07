import pytest
import sqlalchemy as sa
from alembic.command import upgrade
from alembic.config import Config as AlembicConfig
from src.config import Config
from src.database.models import Base
from src.setup import create_postgres_dsn, setup


@pytest.fixture(scope="session")
def test_config():
    config = Config()
    config.pg.db = f'test_{config.pg.db}'
    return config


@pytest.fixture(scope="session", autouse=True)
def upgrade_schema_db(test_config):
    postgres_dsn = create_postgres_dsn(**test_config.pg.model_dump())

    alembic_cfg = AlembicConfig("alembic.ini")
    alembic_cfg.set_main_option("script_location", "../migrations")
    alembic_cfg.set_main_option("sqlalchemy.url", postgres_dsn)

    upgrade(alembic_cfg, "head")


@pytest.fixture(scope='function', autouse=True)
def app(test_config):
    return setup(test_config)


@pytest.fixture(scope="function", autouse=True)
async def clean_tables(app) -> None:
    yield
    session_factory = app.session_factory
    async with session_factory() as session:
        for table in Base.metadata.tables:
            await session.execute(sa.text(f"TRUNCATE TABLE {table} CASCADE;"))
        await session.commit()


@pytest.fixture(scope="function")
async def client(aiohttp_client, app):
    yield await aiohttp_client(app)
