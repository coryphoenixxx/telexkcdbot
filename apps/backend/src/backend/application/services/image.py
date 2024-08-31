import logging
from dataclasses import dataclass

from backend.core.value_objects import TranslationImageID
from backend.infrastructure.database.repositories import TranslationImageRepo
from backend.infrastructure.database.transaction import TransactionManager
from backend.infrastructure.filesystem.translation_image_file_manager import (
    TranslationImageFileManager,
)
from backend.infrastructure.image_converter import ImageConversionError, ImageConverter

logger = logging.getLogger(__name__)


@dataclass(slots=True, eq=False, frozen=True)
class TranslationImageService:
    repo: TranslationImageRepo
    transaction: TransactionManager
    file_manager: TranslationImageFileManager
    converter: ImageConverter

    async def convert_and_update(self, image_id: TranslationImageID) -> None:
        image_dto = await self.repo.get_by_id(image_id)
        image_abs_path = self.file_manager.rel_to_abs(image_dto.original)

        try:
            converted_abs_path = self.converter.convert_to_webp(image_abs_path)
        except ImageConversionError as err:
            logger.warning(err.message)
        else:
            converted_rel_path = self.file_manager.abs_to_rel(converted_abs_path)
            await self.repo.update_converted(image_id, converted_rel_path)
            await self.transaction.commit()
