from sqlalchemy.ext.asyncio import AsyncSession


class ComicRepo:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, comic_base_dto):
        ...
