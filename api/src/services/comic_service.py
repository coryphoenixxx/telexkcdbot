from sqlalchemy.exc import DatabaseError
from src import dtos
from src.helpers.exceptions import CustomError, NotFoundError
from src.repositories.comic_repository import ComicRepository
from src.repositories.image_repository import ImageRepository


class ComicService:
    def __init__(self, comic_repo: ComicRepository, image_repo: ImageRepository | None):
        self._comic_repo = comic_repo
        self._image_repo = image_repo

    async def create_comic(
            self,
            comic_dto: dtos.ComicOriginRequestDTO,
    ) -> dtos.ComicResponseDto:
        if self._image_repo:
            comic_dto.text_data.image_url = self._image_repo.rel_path

        try:
            return (await self._comic_repo.create(comic_dto)).to_dto()
        except DatabaseError as err:
            if self._image_repo:
                await self._image_repo.delete()
            err_msg = str(err.orig)
            if 'comics_pkey' in err_msg:  # TODO: create sqla convention
                raise CustomError("Comic already exists!")
            elif 'uix__comics' in err_msg:
                raise CustomError("Comic with same title already exists!")

    async def get_comic_by_id(self, comic_id: int) -> dtos.ComicResponseDto:
        comic = await self._comic_repo.get_by_id(comic_id)

        if not comic:
            raise NotFoundError

        return comic.to_dto()
