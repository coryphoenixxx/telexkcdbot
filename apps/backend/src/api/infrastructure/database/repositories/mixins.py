
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.application.exceptions.translation import (
    TranslationImagesAlreadyAttachedError,
    TranslationImagesNotCreatedError,
)
from api.application.types import TranslationID, TranslationImageID
from api.infrastructure.database.models import TranslationImageModel


class GetImagesMixin:
    async def _get_images(
        self,
        session: AsyncSession,
        image_ids: list[TranslationImageID],
        translation_id: TranslationID | None = None,
    ) -> list[TranslationImageModel]:
        if not image_ids:
            return []

        image_ids = set(image_ids)

        stmt = select(TranslationImageModel).where(
            TranslationImageModel.image_id.in_(image_ids),
        )
        image_models = (await session.scalars(stmt)).all()

        if diff := image_ids - {m.image_id for m in image_models}:
            raise TranslationImagesNotCreatedError(image_ids=sorted(diff))

        if another_owner_ids := {
            m.translation_id
            for m in image_models
            if m.translation_id and m.translation_id != translation_id
        }:
            raise TranslationImagesAlreadyAttachedError(
                translation_ids=sorted(another_owner_ids),
                image_ids=sorted(image_ids),
            )

        return list(image_models)
