from pathlib import Path

from api.application.dtos.responses.image import TranslationImageOrphanResponseDTO
from api.application.image_saver import ImageSaveHelper
from api.infrastructure.database import TranslationImageGateway, UnitOfWork
from api.my_types import TranslationImageID
from api.presentation.my_types import ImageObj, TranslationImageMeta

# from faststream.nats.broker.broker import NatsBroker
# from shared.messages import ImageProcessInMessage


class TranslationImageService:
    def __init__(
        self,
        gateway: TranslationImageGateway,
        uow: UnitOfWork,
        image_saver: ImageSaveHelper,
        # broker: NatsBroker,
    ):
        self._gateway = gateway
        self._uow = uow
        self._image_saver = image_saver
        # self._broker = broker

    async def create(
        self,
        metadata: TranslationImageMeta,
        image: ImageObj | None = None,
    ) -> TranslationImageOrphanResponseDTO:
        original_abs_path, original_rel_path = await self._image_saver.save(metadata, image)

        image_dto = await self._gateway.create(original_rel_path)

        await self._uow.commit()

        # await self._process_image(image_dto.id, original_abs_path)

        return image_dto

    # async def _process_image(self, image_id: TranslationImageID, original_abs_path: Path) -> None:
    #     await self._broker.publish(
    #         message=ImageProcessInMessage(
    #             image_id=image_id,
    #             original_abs_path=original_abs_path,
    #         ),
    #         subject="internal.api.images.process.in",
    #         stream="process_images_in_stream",
    #     )

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
