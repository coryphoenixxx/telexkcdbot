import pytest
import sqlalchemy as sa
from src.config import Config
from src.database.models import Base
from src.setup import create_engine, create_session_factory, setup_app


@pytest.fixture(scope='session')
def test_config():
    config = Config()
    config.pg.db = f'test_{config.pg.db}'
    return config


@pytest.fixture(scope='function')
def engine(test_config):
    return create_engine(test_config)


@pytest.fixture(scope='function')
def session_factory(engine):
    return create_session_factory(engine)


@pytest.fixture(scope='session')
def db_setup_teardown(engine):
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture(scope='function', autouse=True)
def app(test_config):
    return setup_app(test_config)


@pytest.fixture(scope='function', autouse=True)
async def clean_tables(session_factory):
    yield
    async with session_factory() as session:
        for table in Base.metadata.tables:
            await session.execute(sa.text(f"TRUNCATE TABLE {table} CASCADE;"))
        await session.commit()


@pytest.fixture(scope="function")
async def client(aiohttp_client, app):
    yield await aiohttp_client(app)
