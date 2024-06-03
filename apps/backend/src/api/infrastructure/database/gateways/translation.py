from typing import NoReturn

from sqlalchemy import delete, select
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.orm import noload
from sqlalchemy.sql.selectable import ForUpdateArg, ForUpdateParameter

from api.application.dtos.requests.translation import TranslationRequestDTO
from api.application.dtos.responses.translation import TranslationResponseDTO
from api.application.exceptions.comic import ComicByIDNotFoundError
from api.application.exceptions.translation import (
    TranslationAlreadyExistsError,
    TranslationByIDNotFoundError,
    TranslationByLanguageNotFoundError,
)
from api.infrastructure.database.gateways.base import BaseGateway
from api.infrastructure.database.gateways.mixins import GetImagesMixin
from api.infrastructure.database.models import TranslationModel
from api.infrastructure.database.utils import build_searchable_text
from api.my_types import ComicID, Language, TranslationID


class TranslationGateway(BaseGateway, GetImagesMixin):
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
            source_url=dto.source_url,
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
        translation.source_url = dto.source_url
        translation.images = images
        translation.searchable_text = build_searchable_text(dto.title, dto.raw_transcript)

        try:
            await self._session.flush()
        except IntegrityError as err:
            self._handle_db_error(err, comic_id, dto)
        else:
            return TranslationResponseDTO.from_model(translation)

    async def update_draft_status(
        self,
        translation_id: TranslationID,
        new_draft_status: bool,
    ) -> None:
        translation = await self._get_by_id(translation_id, with_for_update=True)
        translation.is_draft = new_draft_status

    async def delete(self, translation_id: TranslationID) -> None:
        stmt = (
            delete(TranslationModel)
            .options(noload(TranslationModel.images))
            .where(TranslationModel.translation_id == translation_id)
            .returning(TranslationModel)
        )

        translation = (await self._session.scalars(stmt)).unique().one_or_none()

        if not translation:
            raise TranslationByIDNotFoundError(translation_id=translation_id)

    async def get_by_id(self, translation_id: TranslationID) -> TranslationResponseDTO:
        return TranslationResponseDTO.from_model(model=await self._get_by_id(translation_id))

    async def get_by_language(self, comic_id, language: Language) -> TranslationResponseDTO:
        stmt = select(TranslationModel).where(
            TranslationModel.comic_id == comic_id,
            TranslationModel.language == language,
        )

        translation = (await self._session.scalars(stmt)).unique().one_or_none()

        if not translation:
            raise TranslationByLanguageNotFoundError(comic_id, language)

        return TranslationResponseDTO.from_model(translation)

    async def _get_by_id(
        self,
        translation_id: TranslationID,
        with_for_update: ForUpdateParameter = False,
    ) -> TranslationModel:
        translation_model = await self._session.get(
            TranslationModel,
            translation_id,
            with_for_update=with_for_update,
        )

        if not translation_model:
            raise TranslationByIDNotFoundError(translation_id=translation_id)

        return translation_model

    def _handle_db_error(
        self,
        err: DBAPIError,
        comic_id: ComicID,
        dto: TranslationRequestDTO,
    ) -> NoReturn:
        match err.__cause__.__cause__.constraint_name:  # type: ignore
            case "uq_translation_if_not_draft":
                raise TranslationAlreadyExistsError(comic_id, dto.language)
            case "fk_translations_comic_id_comics":
                raise ComicByIDNotFoundError(comic_id)
            case _:
                raise err
