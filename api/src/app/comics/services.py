
from sqlalchemy.exc import DatabaseError

from src.core.utils.uow import UOW

from .dtos import ComicCreateDTO
from .image_utils.dtos import ComicImageDTO
from .image_utils.saver import ImageSaver
from .translations.dtos import TranslationCreateDTO


class ComicsService:
    def __init__(self, uow: UOW):
        self._uow = uow

    async def create_comic(
            self,
            comic_base_dto: ComicCreateDTO,
            comic_eng_translation_dto: TranslationCreateDTO,
            temp_images: list[ComicImageDTO | None],
    ):
        async with self._uow:
            try:
                await self._generate_issue_numbers_if_not_exists(comic_base_dto, temp_images)
                await self._uow.comic_repo.create(comic_base_dto)
                for img in temp_images:
                    if img:
                        comic_eng_translation_dto.images[img.type] = ImageSaver(img).db_path
                comic_base_model_id = 1
                await self._uow.comic_translation_repo.add(comic_base_model_id, comic_eng_translation_dto)
                await self._save_images(temp_images)
                await self._uow.commit()
            except DatabaseError:
                ...

    @staticmethod
    async def _save_images(temp_images: list[ComicImageDTO | None]):
        for img in temp_images:
            if img:
                image_saver = ImageSaver(temp_image_dto=img)
                await image_saver.save()

    async def _generate_issue_numbers_if_not_exists(
            self, comic_base_dto: ComicCreateDTO,
            temp_images: list[ComicImageDTO | None],
    ):
        if comic_base_dto.is_extra and not comic_base_dto.issue_number:
            extra_num = await self._uow.comic_repo.get_extra_num()
            issue_number = -(extra_num + 1)
            comic_base_dto.issue_number = issue_number

            for img in temp_images:
                if img:
                    img.issue_number = issue_number
