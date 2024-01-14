from collections.abc import Iterable

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.comics.exceptions import ComicNotFoundError
from src.app.comics.types import ComicID
from src.app.images.models import TranslationImageModel
from src.app.images.types import TranslationImageID

from .dtos.request import TranslationRequestDTO
from .dtos.response import TranslationResponseDTO
from .exceptions import (
    TranslationImagesAlreadyAttachedError,
    TranslationImagesNotCreatedError,
    TranslationUniqueError,
)
from .models import TranslationModel
from .types import TranslationID


class TranslationRepo:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(
        self,
        comic_id: ComicID,
        dto: TranslationRequestDTO,
    ) -> TranslationResponseDTO:
        try:
            images = await self._get_images(dto.images)

            translation = TranslationModel(
                comic_id=comic_id,
                title=dto.title,
                tooltip=dto.tooltip,
                transcript=dto.transcript,
                news_block=dto.news_block,
                language=dto.language,
                is_draft=dto.is_draft,
                images=images,
            )

            self._session.add(translation)
            await self._session.flush()
        except IntegrityError as err:
            self._handle_integrity_error(
                err=err,
                dto=dto,
                comic_id=comic_id,
            )
        else:
            return translation.to_dto()

    async def update(
        self,
        translation_id: TranslationID,
        dto: TranslationRequestDTO,
    ) -> TranslationModel:
        images = await self._get_images(dto.images)

        model: TranslationModel = await self.get_by_id(translation_id)

        model.title = dto.title
        model.tooltip = dto.tooltip
        model.transcript = dto.transcript
        model.news_block = dto.news_block
        model.language = dto.language
        model.is_draft = dto.is_draft
        model.images = images

        return model

    async def get_by_id(self, translation_id: TranslationID) -> TranslationModel:
        stmt = select(TranslationModel).where(
            TranslationModel.id == translation_id,
        )

        return (await self._session.scalars(stmt)).unique().one_or_none()

    async def _get_images(
        self,
        image_ids: list[TranslationImageID],
    ) -> Iterable[TranslationImageModel]:
        if not image_ids:
            return []

        image_ids = set(image_ids)

        stmt = select(TranslationImageModel).where(TranslationImageModel.id.in_(image_ids))

        image_models = (await self._session.scalars(stmt)).all()

        diff = image_ids - {model.id for model in image_models}
        if diff:
            raise TranslationImagesNotCreatedError(image_ids=sorted(diff))

        owner_ids = {model.translation_id for model in image_models if model.translation_id}
        if owner_ids:
            raise TranslationImagesAlreadyAttachedError(
                translation_ids=sorted(owner_ids),
                image_ids=sorted(image_ids),
            )

        return image_models

    @staticmethod
    def _handle_integrity_error(
        err: IntegrityError,
        dto: TranslationRequestDTO,
        comic_id: ComicID,
    ):
        constraint = err.__cause__.__cause__.constraint_name
        if constraint == "uq_translation_if_not_draft":
            raise TranslationUniqueError(
                comic_id=comic_id,
                language=dto.language,
            )
        elif constraint == "fk_translations_comic_id_comics":
            raise ComicNotFoundError(comic_id)
        raise err
