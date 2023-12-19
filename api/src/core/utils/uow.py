from functools import cached_property
from types import TracebackType

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.app.comics.repo import ComicRepo
from src.app.comics.translations.repo import TranslationRepo


class UOW:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self._session_factory = session_factory

    @cached_property
    def comic_repo(self) -> ComicRepo:
        return ComicRepo(self._session)

    @cached_property
    def translation_repo(self) -> TranslationRepo:
        return TranslationRepo(self._session)

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

    async def commit(self):
        await self._session.commit()

    async def rollback(self):
        await self._session.rollback()
