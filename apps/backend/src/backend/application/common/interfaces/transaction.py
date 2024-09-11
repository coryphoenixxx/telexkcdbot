from typing import Protocol


class TransactionManagerInterface(Protocol):
    async def commit(self) -> None: ...

    async def rollback(self) -> None: ...
