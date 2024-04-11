from sqlalchemy import delete
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.orm import noload
from sqlalchemy.sql.selectable import ForUpdateArg, ForUpdateParameter

from api.application.dtos.requests.translation import TranslationRequestDTO
from api.application.dtos.responses.translation import TranslationResponseDTO
from api.application.exceptions.comic import ComicByIDNotFoundError
from api.application.exceptions.translation import (
    TranslationAlreadyExistsError,
    TranslationNotFoundError,
)
from api.infrastructure.database.models import TranslationModel
from api.infrastructure.database.repositories.base import BaseRepo
from api.infrastructure.database.repositories.mixins import GetImagesMixin
from api.infrastructure.database.utils import build_searchable_text
from api.types import ComicID, TranslationID


class TranslationRepo(BaseRepo, GetImagesMixin):
    async def add(
        self,
        comic_id: ComicID,
        dto: TranslationRequestDTO,
    ) -> TranslationResponseDTO:
        images = await self._get_images_by_ids(dto.image_ids)

        translation = TranslationModel(
            comic_id=comic_id,
            title=dto.title,
            language=dto.language,
            tooltip=dto.tooltip,
            raw_transcript=dto.raw_transcript,
            translator_comment=dto.translator_comment,
            source_link=dto.source_link,
            is_draft=dto.is_draft,
            images=images,
            searchable_text=build_searchable_text(dto.title, dto.raw_transcript, dto.is_draft),
        )

        self._session.add(translation)

        try:
            await self._session.flush()
        except IntegrityError as err:
            self._handle_db_error(err, comic_id, dto)
        else:
            return TranslationResponseDTO.from_model(model=translation)

    async def update(
        self,
        translation_id: TranslationID,
        dto: TranslationRequestDTO,
    ) -> TranslationResponseDTO:
        images = await self._get_images_by_ids(dto.image_ids, translation_id)

        translation = await self._get_by_id(
            translation_id,
            with_for_update=ForUpdateArg(of=TranslationModel),
        )

        comic_id = translation.comic_id

        translation.title = dto.title
        translation.language = dto.language
        translation.tooltip = dto.tooltip
        translation.raw_transcript = dto.raw_transcript
        translation.translator_comment = dto.translator_comment
        translation.source_link = dto.source_link
        translation.images = images
        translation.searchable_text = build_searchable_text(dto.title, dto.raw_transcript)
        translation.is_draft = dto.is_draft

        try:
            await self._session.flush()
        except IntegrityError as err:
            self._handle_db_error(err, comic_id, dto)
        else:
            return TranslationResponseDTO.from_model(translation)

    async def delete(self, translation_id: TranslationID) -> None:
        stmt = (
            delete(TranslationModel)
            .options(noload(TranslationModel.images))
            .where(TranslationModel.translation_id == translation_id)
            .returning(TranslationModel)
        )

        translation = (await self._session.scalars(stmt)).unique().one_or_none()

        if not translation:
            raise TranslationNotFoundError(translation_id=translation_id)

    async def get_by_id(self, translation_id: TranslationID) -> TranslationResponseDTO:
        translation = await self._get_by_id(translation_id)

        return TranslationResponseDTO.from_model(translation)

    async def _get_by_id(
        self,
        translation_id: TranslationID,
        with_for_update: ForUpdateParameter = False,
    ) -> TranslationModel:
        translation = await self._session.get(
            TranslationModel,
            translation_id,
            with_for_update=with_for_update,
        )

        if not translation:
            raise TranslationNotFoundError(translation_id=translation_id)

        return translation

    def _handle_db_error(
        self,
        err: DBAPIError,
        comic_id: ComicID,
        dto: TranslationRequestDTO,
    ) -> None:
        constraint_name = err.__cause__.__cause__.constraint_name

        if constraint_name == "uq_translation_if_not_draft":
            raise TranslationAlreadyExistsError(comic_id, dto.language)
        elif constraint_name == "fk_translations_comic_id_comics":
            raise ComicByIDNotFoundError(comic_id)

        raise err
