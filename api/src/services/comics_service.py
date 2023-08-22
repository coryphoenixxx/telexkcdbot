from src import dtos
from src.database.repositories import ComicsRepo
from src.utils.exceptions import NotFoundError


class ComicsService:
    def __init__(self, comic_repo: ComicsRepo):
        self._repo = comic_repo

    async def get_comic_by_id(self, comic_id: int) -> dtos.ComicResponse:
        comic = await self._repo.get_by_id(comic_id)

        if not comic:
            raise NotFoundError

        return comic.to_dto()

    async def get_comic_list(self):
        ...

    async def create_comic(self, comic_dto: dtos.ComicRequest) -> dtos.ComicResponse:
        comic = await self._repo.create(comic_dto)
        return comic.to_dto()

    async def delete_comic(self):
        ...

    async def search_comics_by_q(self):
        ...
