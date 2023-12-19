from sqlalchemy.ext.asyncio import AsyncSession

from src.app.comics.translations.dtos import TranslationCreateDTO


class ComicTranslationRepo:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def add(self, issue_number: int, translation: TranslationCreateDTO):
        ...
