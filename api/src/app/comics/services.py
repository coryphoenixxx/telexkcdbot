from src.core.database import DatabaseHolder

from .dtos import ComicCreateTotalDTO, ComicGetDTO
from .exceptions import ComicNotFoundError


class ComicService:
    def __init__(self, holder: DatabaseHolder):
        self._holder = holder

    async def create_comic(
            self,
            comic_dto: ComicCreateTotalDTO,
    ) -> ComicGetDTO:
        async with self._holder:
            comic_id = await self._holder.comic_repo.create(comic_dto.comic_base)

            await self._holder.translation_repo.add_to_comic(comic_id, comic_dto.en_translation)

            await self._holder.commit()

            comic_model = await self._holder.comic_repo.get_by_id(comic_id)

        return ComicGetDTO.from_model(comic_model)

    async def get_comic_by_id(self, comic_id: int) -> ComicGetDTO:
        async with self._holder:
            comic_model = await self._holder.comic_repo.get_by_id(comic_id)

        if not comic_model:
            raise ComicNotFoundError(comic_id=comic_id)

        return ComicGetDTO.from_model(comic_model)
