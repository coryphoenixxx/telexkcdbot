from sqlalchemy.ext.asyncio import AsyncSession


class ComicTranslationRepo:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def add(self, comic_translation_dto):
        ...
