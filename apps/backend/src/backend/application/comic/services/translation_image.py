import logging
from dataclasses import dataclass

from backend.application.comic.exceptions import ImageConversionError, TranslationImageNotFoundError
from backend.application.comic.interfaces import (
    ImageConverterInterface,
    TranslationImageFileManagerInterface,
    TranslationImageRepoInterface,
)
from backend.application.common.interfaces import TransactionManagerInterface
from backend.core.value_objects import TranslationImageID

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class TranslationImageService:
    repo: TranslationImageRepoInterface
    transaction: TransactionManagerInterface
    file_manager: TranslationImageFileManagerInterface
    converter: ImageConverterInterface

    async def convert_and_update(self, image_id: TranslationImageID) -> None:
        image_dto = await self.repo.get_by_id(image_id)

        if image_dto is None:
            raise TranslationImageNotFoundError(image_id)

        image_abs_path = self.file_manager.rel_to_abs(image_dto.original)

        try:
            converted_abs_path = self.converter.convert_to_webp(image_abs_path)
        except ImageConversionError as err:
            logger.warning(err.message)
        else:
            converted_rel_path = self.file_manager.abs_to_rel(converted_abs_path)
            await self.repo.update_converted(image_id, converted_rel_path)
            await self.transaction.commit()
