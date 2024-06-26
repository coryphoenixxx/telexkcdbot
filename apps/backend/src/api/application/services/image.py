from pathlib import Path

from api.application.dtos.common import ImageObj, TranslationImageMeta
from api.application.dtos.responses import TranslationImageOrphanResponseDTO
from api.core.value_objects import TranslationImageID
from api.infrastructure.database.repositories import TranslationImageRepo
from api.infrastructure.database.transaction import TransactionManager
from api.infrastructure.image_saver import ImageSaveHelper


class TranslationImageService:
    def __init__(
        self,
        repo: TranslationImageRepo,
        transaction: TransactionManager,
        image_saver: ImageSaveHelper,
    ) -> None:
        self._repo = repo
        self._transaction = transaction
        self._image_saver = image_saver

    async def create(
        self,
        metadata: TranslationImageMeta,
        image: ImageObj | None = None,
    ) -> tuple[Path, TranslationImageOrphanResponseDTO]:
        original_abs_path, original_rel_path = await self._image_saver.save(metadata, image)

        image_dto = await self._repo.create(original_rel_path)

        await self._transaction.commit()

        return original_abs_path, image_dto

    async def update(
        self,
        image_id: TranslationImageID,
        converted_abs_path: Path | None,
        thumbnail_abs_path: Path,
    ) -> None:
        await self._repo.update(
            image_id=image_id,
            converted_rel_path=self._image_saver.cut_rel_path(converted_abs_path),
            thumbnail_rel_path=self._image_saver.cut_rel_path(thumbnail_abs_path),
        )
        await self._transaction.commit()
