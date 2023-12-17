from sqlalchemy.ext.asyncio import AsyncSession

from src.app.comics.dtos import ComicCreateDTO
from src.app.comics.models import Comic


class ComicRepo:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, comic_base_dto: ComicCreateDTO) -> Comic:
        ...

    async def get_extra_num(self) -> int:
        return 0
