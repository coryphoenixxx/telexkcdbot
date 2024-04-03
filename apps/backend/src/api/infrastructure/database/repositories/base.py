from sqlalchemy.ext.asyncio import AsyncSession


class BaseRepo:
    def __init__(self, session: AsyncSession):
        self._session = session
