from functools import cached_property
from types import TracebackType

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from api.infrastructure.database import ComicGateway, TranslationGateway, TranslationImageGateway


class DatabaseHolder:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self._session_factory = session_factory

    @cached_property
    def comic_repo(self) -> ComicGateway:
        return ComicGateway(self._session)

    @cached_property
    def translation_repo(self) -> TranslationGateway:
        return TranslationGateway(self._session)

    @cached_property
    def translation_image_repo(self) -> TranslationImageGateway:
        return TranslationImageGateway(self._session)

    async def __aenter__(self) -> None:
        self._session: AsyncSession = self._session_factory()

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        if exc_type:
            await self.rollback()
        await self._session.close()

    async def commit(self) -> None:
        await self._session.commit()

    async def rollback(self) -> None:
        await self._session.rollback()
