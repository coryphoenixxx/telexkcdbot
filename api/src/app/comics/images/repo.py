from sqlalchemy.ext.asyncio import AsyncSession

from .dtos import TranslationImageDTO
from .models import TranslationImageModel


class TranslationImageRepo:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, image_dto: TranslationImageDTO, image_save_path: str) -> int:
        async with self._session:  # type: AsyncSession
            translation_image_model = TranslationImageModel(
                version=image_dto.version,
                path=image_save_path,
                dimensions=image_dto.image_obj.dimensions,
            )

            self._session.add(translation_image_model)
            await self._session.flush()
            image_id = translation_image_model.id
            await self._session.commit()
        return image_id
