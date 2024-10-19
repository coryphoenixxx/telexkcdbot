import logging
from dataclasses import dataclass
from pathlib import Path

from backend.application.common.interfaces import (
    ImageFileManagerInterface,
    StreamReaderProtocol,
    TempFileManagerInterface,
    TransactionManagerInterface,
)
from backend.application.image.exceptions import ImageConversionError
from backend.application.image.interfaces import ImageFileProcessorInterface, ImageRepoInterface
from backend.domain.entities.image import ImageMeta, NewImageEntity
from backend.domain.value_objects import ImageFileObj, ImageId

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class UploadImageInteractor:
    temp_file_manager: TempFileManagerInterface
    image_repo: ImageRepoInterface
    transaction: TransactionManagerInterface

    async def execute(self, source: StreamReaderProtocol | Path) -> ImageId:
        if isinstance(source, Path):
            temp_image_id = self.temp_file_manager.safe_move(source)
        else:
            temp_image_id = await self.temp_file_manager.read_from_stream(source, 1024 * 64)

        image_file_obj = ImageFileObj(source=self.temp_file_manager.get_abs_path(temp_image_id))
        image_file_obj.validate_securely()

        image_id = await self.image_repo.create(
            NewImageEntity(
                temp_image_id=temp_image_id,
                meta=ImageMeta(
                    format=image_file_obj.format,
                    size=image_file_obj.size,
                    dimensions=image_file_obj.dimensions,
                ),
            )
        )

        await self.transaction.commit()

        return image_id


@dataclass(slots=True)
class ConvertImageInteractor:
    image_repo: ImageRepoInterface
    temp_file_manager: TempFileManagerInterface
    image_file_manager: ImageFileManagerInterface
    image_processor: ImageFileProcessorInterface
    transaction: TransactionManagerInterface

    async def execute(self, image_id: ImageId) -> None:
        image = await self.image_repo.load(image_id)

        old_image_path = image.image_path

        if old_image_path:
            original_image_file = ImageFileObj(
                source=self.temp_file_manager.get_abs_path(
                    image.temp_image_id,  # type: ignore[arg-type]
                )
            )

            try:
                converted_image_file = self.image_processor.convert_to_webp(original_image_file)
            except ImageConversionError as err:
                logger.warning(err.message)
            else:
                converted_rel_path = image.image_path.with_name(  # type: ignore[union-attr]
                    image.image_path.stem + "_converted"  # type: ignore[union-attr]
                ).with_suffix(".webp")

                await self.image_file_manager.save(converted_image_file, converted_rel_path)

                image.image_path = converted_rel_path

                await self.image_repo.update(image)

                await self.transaction.commit()

                await self.image_file_manager.delete(old_image_path)

                converted_image_file.source.unlink()

            original_image_file.source.unlink()
