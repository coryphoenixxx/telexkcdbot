from api.core.database import DatabaseHolder

from .dtos import TranslationImageRequestDTO
from .types import TranslationImageID
from .utils import ImageFileSaver


class TranslationImageService:
    def __init__(self, db_holder: DatabaseHolder, image_saver: ImageFileSaver):
        self._db_holder = db_holder
        self._image_saver = image_saver

    async def create(self, image_dto: TranslationImageRequestDTO) -> TranslationImageID:
        async with self._db_holder:
            _, rel_saved_path = await self._image_saver.save(image_dto)

            image_id = await self._db_holder.translation_image_repo.create(
                image_dto, rel_saved_path,
            )

            await self._db_holder.commit()
            return image_id
