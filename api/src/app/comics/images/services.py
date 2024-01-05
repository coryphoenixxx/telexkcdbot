from src.core.database import DatabaseHolder

from .dtos import TranslationImageDTO
from .types import TranslationImageId
from .utils import ImageFileSaver


class TranslationImageService:
    def __init__(self, db_holder: DatabaseHolder, file_saver: ImageFileSaver):
        self._db_holder = db_holder
        self._file_saver = file_saver

    async def create(self, image_dto: TranslationImageDTO) -> TranslationImageId:
        async with self._db_holder:
            image_rel_path = await self._file_saver.save(image_dto)

            image_id = await self._db_holder.translation_image_repo.create(
                image_dto, image_rel_path,
            )

            await self._db_holder.commit()
            return image_id
