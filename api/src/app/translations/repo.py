from collections.abc import Iterable

from sqlalchemy import false, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.comics.types import ComicID
from src.app.images.models import TranslationImageModel
from src.app.images.types import TranslationImageID
from src.core.types import Language

from .dtos import TranslationRequestDTO, TranslationResponseDTO
from .exceptions import TranslationImagesNotCreatedError, TranslationTitleUniqueError
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

    async def get_id_by_comic_id_and_lang(
        self, comic_id: ComicID, language: Language,
    ) -> TranslationID:
        stmt = select(TranslationModel.id).where(
            TranslationModel.comic_id == comic_id,
            TranslationModel.language == language,
            TranslationModel.is_draft == false(),
        )

        return await self._session.scalar(stmt)

    async def get_by_id(self, translation_id: TranslationID):
        stmt = select(TranslationModel).where(
            TranslationModel.id == translation_id,
        )

        return (await self._session.scalars(stmt)).unique().one_or_none()

    async def _get_images(
        self, images: list[TranslationImageID],
    ) -> Iterable[TranslationImageModel]:
        if not images:
            return []

        stmt = select(TranslationImageModel).where(
            TranslationImageModel.id.in_(images),
        )

        image_models = (await self._session.scalars(stmt)).all()

        diff = set(images) - {model.id for model in image_models}
        if diff:
            raise TranslationImagesNotCreatedError(image_ids=sorted(diff))

        return image_models

    def _handle_integrity_error(self, err: IntegrityError, dto: TranslationRequestDTO):
        constraint = err.__cause__.__cause__.constraint_name
        if constraint == "uq_translation_title_if_not_draft":
            raise TranslationTitleUniqueError(
                title=dto.title,
                language=dto.language,
            )
        raise err
