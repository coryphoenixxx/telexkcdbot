import logging
from dataclasses import dataclass

from backend.application.comic.exceptions import ImageConversionError
from backend.application.comic.interfaces import (
    ImageConverterInterface,
    ImageFileManagerInterface,
    TranslationImageRepoInterface,
)
from backend.application.common.interfaces import (
    TempFileManagerInterface,
    TransactionManagerInterface,
)
from backend.application.common.interfaces.file_storages import TempFileID
from backend.core.value_objects import ImageObj, TranslationImageID

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class ProcessTranslationImageInteractor:
    translation_image_repo: TranslationImageRepoInterface
    temp_file_manager: TempFileManagerInterface
    image_file_manager: ImageFileManagerInterface
    converter: ImageConverterInterface
    transaction: TransactionManagerInterface

    async def execute(
        self,
        temp_image_id: TempFileID,
        translation_image_id: TranslationImageID,
    ) -> None:
        original = ImageObj(self.temp_file_manager.get_abs_path(temp_image_id))

        try:
            converted = self.converter.convert_to_webp(original)
        except ImageConversionError as err:
            logger.warning(err.message)
        else:
            if image_dto := await self.translation_image_repo.get_by_id(translation_image_id):
                original_rel_path = image_dto.original
                converted_rel_path = original_rel_path.with_name(
                    original_rel_path.stem + "_converted"
                ).with_suffix(".webp")

                await self.image_file_manager.persist(
                    image=converted,
                    save_path=converted_rel_path,
                )

                await self.translation_image_repo.set_converted_path(
                    translation_image_id=translation_image_id,
                    converted_rel_path=converted_rel_path,
                )

                await self.transaction.commit()

            converted.source.unlink()
        original.source.unlink()
