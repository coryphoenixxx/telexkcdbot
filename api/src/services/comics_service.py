from sqlalchemy.exc import IntegrityError
from src import dtos
from src.database.exceptions import AlreadyExistsError, NotFoundError, SameTextInfoError
from src.database.repositories import ComicFilesRepo, ComicsRepo


class ComicsService:
    def __init__(self, repo: ComicsRepo):
        self._repo = repo

    async def create_comic(
            self,
            comic_dto: dtos.ComicRequestDto,
            image_objs: list[dtos.ImageObjDto],
    ) -> dtos.ComicResponseDto:
        image_service = ComicFilesService(ComicFilesRepo())
        for image in image_objs:
            image_path = await image_service.save_image(image)
            comic_dto.translations[image.language].image_url = image_path

        try:
            comic_model = await self._repo.create(comic_dto)
        except IntegrityError as err:
            if 'comics_pkey' in str(err.orig):
                raise AlreadyExistsError
            elif 'uix__comics' in str(err.orig):
                raise SameTextInfoError
            else:
                ...
        else:
            return comic_model.to_dto()

    async def get_comic_by_id(self, comic_id: int) -> dtos.ComicResponseDto:
        comic = await self._repo.get_by_id(comic_id)

        if not comic:
            raise NotFoundError

        return comic.to_dto()

    async def get_comic_list(self):
        ...

    async def delete_comic(self):
        ...

    async def search_comics_by_q(self):
        ...


class ComicFilesService:
    def __init__(self, repo: ComicFilesRepo):
        self._repo = repo

    async def save_image(self, image_obj: dtos.ImageObjDto):
        return await self._repo.save(image_obj.dst_path, image_obj.image_binary)
