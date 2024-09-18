from collections.abc import AsyncGenerator, Generator
from typing import Any

import pytest
import uvloop
from alembic.command import upgrade
from alembic.config import Config as AlembicConfig
from dishka import AsyncContainer, make_async_container
from pytest_asyncio import is_async_test
from testcontainers.nats import NatsContainer
from testcontainers.postgres import PostgresContainer

from backend.main.ioc.providers import (
    ComicServicesProvider,
    FileManagersProvider,
    FilesystemConfigProvider,
    PublisherRouterProvider,
    RepositoriesProvider,
    TransactionManagerProvider,
)

from .test_providers import TestDbConfigProvider, TestNatsConfigProvider


def pytest_collection_modifyitems(items: Any) -> None:
    """Run all tests in the session in the same event loop"""
    pytest_asyncio_tests = (item for item in items if is_async_test(item))
    session_scope_marker = pytest.mark.asyncio(loop_scope="session")
    for async_test in pytest_asyncio_tests:
        async_test.add_marker(session_scope_marker, append=False)


@pytest.fixture(scope="session")
def event_loop_policy() -> uvloop.EventLoopPolicy:
    return uvloop.EventLoopPolicy()


@pytest.fixture(scope="session")
def postgres_url() -> Generator[str, None, None]:
    with PostgresContainer(
        "groonga/pgroonga:3.2.2-alpine-16",
        driver="asyncpg",
    ) as postgres:
        yield postgres.get_connection_url()


@pytest.fixture(scope="session")
def nats_uri() -> Generator[str, None, None]:
    with NatsContainer("nats:2.10.20").with_command("-js") as nats:
        yield nats.nats_uri()


@pytest.fixture(scope="session", autouse=True)
def make_migrations(postgres_url: str) -> None:
    alembic_config = AlembicConfig("alembic.ini")
    alembic_config.set_main_option("sqlalchemy.url", postgres_url)
    upgrade(alembic_config, "head")


@pytest.fixture(scope="session")
async def container(postgres_url: str, nats_uri: str) -> AsyncGenerator[AsyncContainer, None]:
    container = make_async_container(
        TestDbConfigProvider(postgres_url),
        TestNatsConfigProvider(nats_uri),
        FilesystemConfigProvider(),
        TransactionManagerProvider(),
        FileManagersProvider(),
        RepositoriesProvider(),
        PublisherRouterProvider(),
        ComicServicesProvider(),
    )
    yield container
    await container.close()
