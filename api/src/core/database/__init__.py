import logging
from functools import cached_property
from types import TracebackType

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.app.comics.images.repo import TranslationImageRepo
from src.app.comics.repo import ComicRepo
from src.app.comics.translations.repo import TranslationRepo
from src.core.settings import DbConfig


def create_engine(config: DbConfig) -> AsyncEngine:
    return create_async_engine(
        url=config.pg.dsn,
        echo=config.sqla.echo,
        echo_pool=config.sqla.echo,
        pool_size=config.sqla.pool_size,
    )


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
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


class DatabaseHolder:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self._session_factory = session_factory

    @cached_property
    def comic_repo(self) -> ComicRepo:
        return ComicRepo(self._session)

    @cached_property
    def translation_repo(self) -> TranslationRepo:
        return TranslationRepo(self._session)

    @cached_property
    def translation_image_repo(self) -> TranslationImageRepo:
        return TranslationImageRepo(self._session)

    async def __aenter__(self):
        self._session: AsyncSession = self._session_factory()

    async def __aexit__(
            self,
            exc_type: type[BaseException] | None,
            exc_val: BaseException | None,
            exc_tb: TracebackType | None,
    ):
        if exc_type:
            await self.rollback()
        await self._session.close()

    async def commit(self) -> None:
        await self._session.commit()

    async def rollback(self) -> None:
        await self._session.rollback()
