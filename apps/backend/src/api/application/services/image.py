from pathlib import Path

from api.application.dtos.common import ImageObj, TranslationImageMeta
from api.application.dtos.responses import TranslationImageOrphanResponseDTO
from api.core.entities import TranslationImageID
from api.infrastructure.database.gateways import TranslationImageGateway
from api.infrastructure.database.uow import UnitOfWork
from api.infrastructure.image_saver import ImageSaveHelper


class TranslationImageService:
    def __init__(
        self,
        gateway: TranslationImageGateway,
        uow: UnitOfWork,
        image_saver: ImageSaveHelper,
    ):
        self._gateway = gateway
        self._uow = uow
        self._image_saver = image_saver

    async def create(
        self,
        metadata: TranslationImageMeta,
        image: ImageObj | None = None,
    ) -> tuple[Path, TranslationImageOrphanResponseDTO]:
        original_abs_path, original_rel_path = await self._image_saver.save(metadata, image)

        image_dto = await self._gateway.create(original_rel_path)

        await self._uow.commit()

        return original_abs_path, image_dto

    async def update(
        self,
        image_id: TranslationImageID,
        converted_abs_path: Path | None,
        thumbnail_abs_path: Path,
    ):
        await self._gateway.update(
            image_id=image_id,
            converted_rel_path=self._image_saver.cut_rel_path(converted_abs_path),
            thumbnail_rel_path=self._image_saver.cut_rel_path(thumbnail_abs_path),
        )
        await self._uow.commit()
