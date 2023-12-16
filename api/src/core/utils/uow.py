from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.app.comics.repositories import ComicRepo
from src.app.comics.translations.repositories import ComicTranslationRepo


class UOW:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self._session_factory = session_factory

    @property
    def comic_repo(self):
        return ComicRepo(self._session)

    @property
    def comic_translation_repo(self):
        return ComicTranslationRepo(self._session)

    async def __aenter__(self):
        self._session: AsyncSession = self._session_factory()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            await self.rollback()
        await self._session.close()

    async def commit(self):
        await self._session.commit()

    async def rollback(self):
        await self._session.rollback()
