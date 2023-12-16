from sqlalchemy.exc import DatabaseError

from src.core.utils.uow import UOW

from .dtos import ComicCreateDTO
from .image_utils.dtos import ComicImageDTO
from .image_utils.saver import ImageSaver


class ComicsService:
    def __init__(self, uow: UOW):
        self._uow = uow

    async def create_comic(
        self,
        comic_dto: ComicCreateDTO,
        temp_images: list[ComicImageDTO],
    ):
        for img in temp_images:
            if img:
                image_saver = ImageSaver(temp_image_dto=img)
                await image_saver.save()

        async with self._uow:
            try:
                await self._uow.comic_repo.create(comic_dto.base)
                await self._uow.comic_translation_repo.add(comic_dto.translation)
                await self._uow.commit()
            except DatabaseError:
                ...
            except Exception:
                ...
