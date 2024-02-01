from pathlib import Path

from faststream.nats import NatsBroker
from shared.types import ImageProcessInMessage

from api.core.database import DatabaseHolder

from .dtos import (
    ImageObj,
    TranslationImageMeta,
)
from .types import TranslationImageID
from .utils import ImageSaveHelper


class TranslationImageService:
    def __init__(
        self,
        db_holder: DatabaseHolder,
        image_saver: ImageSaveHelper,
        broker: NatsBroker | None = None,
    ):
        self._db_holder = db_holder
        self._image_saver = image_saver
        self._broker = broker

    async def create(
        self,
        meta: TranslationImageMeta,
        image: ImageObj | None = None,
    ) -> TranslationImageID:
        original_abs_path, original_rel_path = await self._image_saver.save(meta, image)

        async with self._db_holder:
            image_id = await self._db_holder.translation_image_repo.create(
                original_rel_path=original_rel_path,
            )

            if not self._broker:
                ...  # handle

            await self._broker.publish(
                message=ImageProcessInMessage(
                    image_id=image_id,
                    original_abs_path=original_abs_path,
                ),
                subject="image_processing",
                stream="stream",
            )

            await self._db_holder.commit()

            return image_id

    async def update(
        self,
        image_id: TranslationImageID,
        converted_abs_path: Path | None,
        thumbnail_abs_path: Path,
    ):
        async with self._db_holder:
            await self._db_holder.translation_image_repo.update(
                image_id=image_id,
                converted_rel_path=self._image_saver.cut_rel_path(converted_abs_path),
                thumbnail_rel_path=self._image_saver.cut_rel_path(thumbnail_abs_path),
            )
            await self._db_holder.commit()
