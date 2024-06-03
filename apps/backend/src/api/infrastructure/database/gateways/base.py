from sqlalchemy.ext.asyncio import AsyncSession


class BaseGateway:
    def __init__(self, session: AsyncSession):
        self._session = session
