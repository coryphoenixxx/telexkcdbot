from collections.abc import Iterable

from shared.types import LanguageCode
from sqlalchemy import delete, select
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.orm import noload

from api.application.dtos.requests.translation import TranslationRequestDTO
from api.application.dtos.responses.translation import TranslationResponseDTO
from api.application.exceptions.comic import ComicByIDNotFoundError
from api.application.exceptions.translation import (
    TranslationAlreadyExistsError,
    TranslationNotFoundError,
)
from api.application.types import TranslationID
from api.infrastructure.database.models import ComicModel, TranslationImageModel, TranslationModel
from api.infrastructure.database.repositories.base import BaseRepo
from api.infrastructure.database.repositories.mixins import GetImagesMixin
from api.infrastructure.database.utils import build_searchable_text
from api.utils import slugify


class TranslationRepo(BaseRepo, GetImagesMixin):
    async def create(self, dto: TranslationRequestDTO) -> TranslationResponseDTO:
        translation = TranslationModel(
            comic_id=dto.comic_id,
            title=dto.title,
            language=dto.language,
            tooltip=dto.tooltip,
            transcript_raw=dto.transcript_raw,
            translator_comment=dto.translator_comment,
            source_link=dto.source_link,
            images=await self._get_images(self._session, dto.image_ids),
            is_draft=dto.is_draft,
            searchable_text=build_searchable_text(dto.title, dto.transcript_raw),
            drafts=[],
        )

        self._session.add(translation)

        try:
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
        images: Iterable[TranslationImageModel] = await self._get_images(
            session=self._session,
            image_ids=dto.image_ids,
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

        try:
            await self._session.flush()
        except IntegrityError as err:
            self._handle_db_error(err=err, dto=dto)
        else:
            return TranslationResponseDTO.from_model(model=translation)

    async def delete(self, translation_id: TranslationID):
        stmt = (
            delete(TranslationModel)
            .options(noload(TranslationModel.images))
            .where(TranslationModel.translation_id == translation_id)
            .returning(TranslationModel)
        )

        translation: TranslationModel = (await self._session.scalars(stmt)).unique().one_or_none()

        if not translation:
            raise TranslationNotFoundError(translation_id=translation_id)

    async def _get_by_id(self, translation_id: TranslationID) -> TranslationModel:
        stmt = select(TranslationModel).where(
            TranslationModel.translation_id == translation_id,
        )

        translation: TranslationModel = (await self._session.scalars(stmt)).unique().one_or_none()
        if not translation:
            raise TranslationNotFoundError(translation_id=translation_id)

        return translation

    async def _update_parent_comic_slug(
        self,
        dto: TranslationRequestDTO,
    ):
        stmt = (
            select(ComicModel)
            .where(ComicModel.comic_id == dto.comic_id)
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
