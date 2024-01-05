from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.comics.images.models import TranslationImageModel

from .dtos import TranslationCreateDTO
from .exceptions import TranslationImagesNotCreatedError
from .models import TranslationModel


class TranslationRepo:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def add_to_comic(
            self,
            comic_id,
            translation_dto: TranslationCreateDTO,
    ):
        stmt = (
            select(TranslationImageModel)
            .where(TranslationImageModel.id.in_(translation_dto.image_ids))
        )
        image_models = (await self._session.scalars(stmt)).all()

        if len(image_models) != len(translation_dto.image_ids):
            raise TranslationImagesNotCreatedError

        translation_model = TranslationModel(
            comic_id=comic_id,
            title=translation_dto.title,
            tooltip=translation_dto.tooltip,
            transcript=translation_dto.transcript,
            news_block=translation_dto.news_block,
            language=translation_dto.language,
            is_draft=translation_dto.is_draft,
            images=image_models,
        )

        self._session.add(translation_model)
