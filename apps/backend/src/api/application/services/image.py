from pathlib import Path

from faststream.nats import NatsBroker

from api.application.dtos import TranslationImageResponseDTO
from api.core.value_objects import TranslationImageID
from api.infrastructure.database.repositories import TranslationImageRepo
from api.infrastructure.database.transaction import TransactionManager
from api.infrastructure.filesystem.image_file_manager import ImageFileManager


class TranslationImageService:
    def __init__(
        self,
        repo: TranslationImageRepo,
        transaction: TransactionManager,
        image_file_manager: ImageFileManager,
        broker: NatsBroker,
    ) -> None:
        self._repo = repo
        self._transaction = transaction
        self._image_file_manager = image_file_manager
        self._broker = broker

    async def update(
        self,
        image_id: TranslationImageID,
        converted_abs_path: Path | None,
        thumbnail_abs_path: Path,
    ) -> None:
        await self._repo.update(
            image_id=image_id,
            converted_rel_path=self._image_file_manager.abs_to_rel(converted_abs_path),
            thumbnail_rel_path=self._image_file_manager.abs_to_rel(thumbnail_abs_path),
        )
        await self._transaction.commit()

    async def get_by_id(self, image_id: TranslationImageID) -> TranslationImageResponseDTO:
        return await self._repo.get_by_id(image_id)
