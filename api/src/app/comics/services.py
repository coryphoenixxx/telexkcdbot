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
        comic_dto: ComicCreateDTO,
        images: list[ComicImageDTO],
    ):
        async with self._uow:
            await self._generate_issue_numbers_if_not_exists(comic_dto, images)
            await self._uow.comic_repo.create(comic_dto)

            self._add_image_path_to_translation(images, comic_dto.translation)
            await self._uow.translation_repo.add(comic_dto.translation)

            await self._save_images(images)
            await self._uow.commit()

    @staticmethod
    def _add_image_path_to_translation(
        images: list[ComicImageDTO], translation: TranslationCreateDTO,
    ):
        for img in images:
            translation.images[img.type] = ImageSaver(img).db_path

    @staticmethod
    async def _save_images(temp_images: list[ComicImageDTO]):
        for img in temp_images:
            image_saver = ImageSaver(temp_image_dto=img)
            await image_saver.save()

    async def _generate_issue_numbers_if_not_exists(
        self,
        comic_base_dto: ComicCreateDTO,
        temp_images: list[ComicImageDTO],
    ):
        if comic_base_dto.is_extra and not comic_base_dto.issue_number:
            extra_num = await self._uow.comic_repo.get_extra_num()
            issue_number = -(extra_num + 1)

            comic_base_dto.issue_number = comic_base_dto.translation.issue_number = issue_number
            for img in temp_images:
                img.issue_number = issue_number
