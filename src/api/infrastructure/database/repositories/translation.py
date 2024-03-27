from collections.abc import Iterable

from shared.types import LanguageCode
from sqlalchemy import delete, select
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import noload

from api.application.dtos.requests.translation import TranslationRequestDTO
from api.application.dtos.responses.translation import TranslationResponseDTO
from api.application.exceptions.comic import ComicByIDNotFoundError
from api.application.exceptions.translation import (
    TranslationAlreadyExistsError,
    TranslationImagesAlreadyAttachedError,
    TranslationImagesNotCreatedError,
    TranslationNotFoundError,
)
from api.application.types import TranslationID, TranslationImageID
from api.infrastructure.database.models import ComicModel, TranslationImageModel, TranslationModel
from api.infrastructure.database.utils import build_searchable_text
from api.utils import slugify


class TranslationRepo:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, dto: TranslationRequestDTO) -> TranslationResponseDTO:
        try:
            images = await self._get_images(dto.images)

            translation = TranslationModel(
                comic_id=dto.comic_id,
                title=dto.title,
                language=dto.language,
                tooltip=dto.tooltip,
                transcript_raw=dto.transcript_raw,
                translator_comment=dto.translator_comment,
                source_link=dto.source_link,
                images=images,
                is_draft=dto.is_draft,
                searchable_text=build_searchable_text(dto.title, dto.transcript_raw),
            )

            self._session.add(translation)
            await self._session.flush()
        except IntegrityError as err:
            self._handle_db_error(err=err, dto=dto)
        else:
            return TranslationResponseDTO.from_model(model=translation)

    async def update(
        self,
        translation_id: TranslationID,
        dto: TranslationRequestDTO,
    ) -> TranslationResponseDTO:
        try:
            images: Iterable[TranslationImageModel] = await self._get_images(
                image_ids=dto.images,
                translation_id=translation_id,
            )

            translation: TranslationModel = await self._get_by_id(translation_id)

            if dto.language == LanguageCode.EN and (
                translation.title != dto.title or not dto.is_draft
            ):
                await self._update_parent_comic_slug(dto)

            translation.comic_id = dto.comic_id
            translation.title = dto.title
            translation.language = dto.language
            translation.tooltip = dto.tooltip
            translation.transcript_raw = dto.transcript_raw
            translation.translator_comment = dto.translator_comment
            translation.source_link = dto.source_link
            translation.images = images
            translation.is_draft = dto.is_draft
            translation.searchable_text = build_searchable_text(dto.title, dto.transcript_raw)

            await self._session.flush()
        except IntegrityError as err:
            self._handle_db_error(err=err, dto=dto)
        else:
            return TranslationResponseDTO.from_model(model=translation)

    async def delete(self, translation_id: TranslationID):
        stmt = (
            delete(TranslationModel)
            .options(noload(TranslationModel.images))
            .where(TranslationModel.id == translation_id)
            .returning(TranslationModel)
        )

        translation: TranslationModel = (await self._session.scalars(stmt)).one_or_none()

        if not translation:
            raise TranslationNotFoundError(translation_id=translation_id)

    async def _get_by_id(self, translation_id: TranslationID) -> TranslationModel:
        stmt = select(TranslationModel).where(
            TranslationModel.id == translation_id,
        )

        translation: TranslationModel = (await self._session.scalars(stmt)).unique().one_or_none()
        if not translation:
            raise TranslationNotFoundError(translation_id=translation_id)

        return translation

    async def _get_images(
        self,
        image_ids: list[TranslationImageID],
        translation_id: TranslationID | None = None,
    ) -> Iterable[TranslationImageModel]:
        if not image_ids:
            return []

        image_ids = set(image_ids)

        stmt = select(TranslationImageModel).where(TranslationImageModel.id.in_(image_ids))
        image_models = (await self._session.scalars(stmt)).all()

        if diff := image_ids - {m.id for m in image_models}:
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

        return image_models

    async def _update_parent_comic_slug(
        self,
        dto: TranslationRequestDTO,
    ):
        stmt = (
            select(ComicModel)
            .where(ComicModel.id == dto.comic_id)
            .options(noload(ComicModel.tags), noload(ComicModel.translations))
        )
        comic: ComicModel = (await self._session.scalars(stmt)).unique().one_or_none()

        if not comic:
            raise ComicByIDNotFoundError(comic_id=dto.comic_id)

        comic.slug = slugify(dto.title)

        self._session.add(comic)

    def _handle_db_error(self, err: DBAPIError, dto: TranslationRequestDTO) -> None:
        constraint_name = err.__cause__.__cause__.constraint_name

        if constraint_name == "uq_translation_if_not_draft":
            raise TranslationAlreadyExistsError(dto.comic_id, dto.language)
        elif constraint_name == "fk_translations_comic_id_comics":
            raise ComicByIDNotFoundError(dto.comic_id)

        raise err
