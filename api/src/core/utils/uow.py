from types import TracebackType

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


class UOW:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self._session_factory = session_factory


    async def __aenter__(self):
        self.session: AsyncSession = self._session_factory()

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ):
        if exc_type:
            await self.rollback()
        await self.session.close()

    async def commit(self):
        await self.session.commit()

    async def rollback(self):
        await self.session.rollback()
