from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..images.models import TranslationImageModel
from .dtos import TranslationCreateDTO
from .exceptions import TranslationImagesNotCreatedError
from .models import TranslationModel
from .types import TranslationID


class TranslationRepo:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(
        self,
        translation_dto: TranslationCreateDTO,
    ) -> TranslationID:
        stmt = select(TranslationImageModel).where(
            TranslationImageModel.id.in_(translation_dto.images),
        )
        image_models = (await self._session.scalars(stmt)).all()

        diff = set(translation_dto.images) - {model.id for model in image_models}
        if diff:
            raise TranslationImagesNotCreatedError(image_ids=sorted(diff))

        translation_model = TranslationModel(
            comic_id=translation_dto.comic_id,
            title=translation_dto.title,
            tooltip=translation_dto.tooltip,
            transcript=translation_dto.transcript,
            news_block=translation_dto.news_block,
            language=translation_dto.language,
            is_draft=translation_dto.is_draft,
            images=image_models,
        )

        self._session.add(translation_model)
        await self._session.flush()

        return translation_model.id
