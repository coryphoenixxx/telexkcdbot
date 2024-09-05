from types import TracebackType

from sqlalchemy.ext.asyncio import AsyncSession


class TransactionManager:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def __aenter__(self) -> "TransactionManager":
        return self

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
