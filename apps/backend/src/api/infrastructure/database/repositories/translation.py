import re
from collections.abc import Sequence
from html import unescape
from typing import NoReturn

from sqlalchemy import delete, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.orm import joinedload
from sqlalchemy.orm.interfaces import ORMOption

from api.application.dtos.common import Language
from api.application.dtos.requests import TranslationRequestDTO
from api.application.dtos.responses import TranslationResponseDTO
from api.core.exceptions import (
    ComicNotFoundError,
    TranslationAlreadyExistsError,
    TranslationNotFoundError,
)
from api.core.value_objects import ComicID, TranslationID
from api.infrastructure.database.models import (
    UNIQUE_TRANSLATION_IF_NOT_DRAFT_CONSTRAINT,
    TranslationModel,
)
from api.infrastructure.database.repositories.base import BaseRepo

SQUARE_BRACKETS_PATTERN = re.compile(r"\[.*?]")
HTML_TAG_PATTERN = re.compile(r"<.*?>")
SPEAKER_PATTERN = re.compile(r"^[\[\w -\]]{3,20}: ", re.UNICODE | re.MULTILINE)
SEPARATE_NUMBER_PATTERN = re.compile(r"\s[0-9]+\s")
REPEATED_EMPTIES_PATTERN = re.compile(r"\s\s+")
SINGLE_CHARACTER_PATTERN = re.compile(r"\b.\b")
PUNCTUATION_PATTERN = re.compile(r"[.:;!?,/\"\']")


def build_searchable_text(title: str, raw_transcript: str, is_draft: bool = False) -> str:
    if is_draft:
        return ""

    transcript_text = unescape(unescape(raw_transcript))

    transcript_text = SQUARE_BRACKETS_PATTERN.sub(repl="\n", string=transcript_text)
    transcript_text = HTML_TAG_PATTERN.sub(repl="\n", string=transcript_text)
    transcript_text = SPEAKER_PATTERN.sub(repl="\n", string=transcript_text)
    transcript_text = SEPARATE_NUMBER_PATTERN.sub(repl=" ", string=transcript_text)
    transcript_text = PUNCTUATION_PATTERN.sub(repl=" ", string=transcript_text)

    normalized = "".join(ch for ch in transcript_text if ch.isalnum() or ch == " ")

    normalized = SINGLE_CHARACTER_PATTERN.sub(repl=" ", string=normalized)
    normalized = REPEATED_EMPTIES_PATTERN.sub(repl=" ", string=normalized)

    return (title.lower() + " :: " + normalized.strip().lower())[:3800]


class TranslationRepo(BaseRepo):
    async def create(
        self,
        comic_id: ComicID,
        dto: TranslationRequestDTO,
    ) -> TranslationResponseDTO:
        stmt = (
            insert(TranslationModel)
            .values(
                comic_id=comic_id,
                title=dto.title,
                language=dto.language,
                tooltip=dto.tooltip,
                raw_transcript=dto.raw_transcript,
                translator_comment=dto.translator_comment,
                source_url=dto.source_url,
                is_draft=dto.is_draft,
                searchable_text=build_searchable_text(
                    dto.title,
                    dto.raw_transcript,
                    dto.is_draft,
                ),
            )
            .returning(TranslationModel.translation_id)
        )

        try:
            translation_id = await self._session.scalar(stmt)
        except IntegrityError as err:
            self._handle_db_error(err)
        else:
            return TranslationResponseDTO.from_model(model=await self._get_by_id(translation_id))

    async def update(
        self,
        translation_id: TranslationID,
        dto: TranslationRequestDTO,
    ) -> TranslationResponseDTO:
        stmt = (
            update(TranslationModel)
            .where(TranslationModel.translation_id == translation_id)
            .values(
                title=dto.title,
                language=dto.language,
                tooltip=dto.tooltip,
                raw_transcript=dto.raw_transcript,
                translator_comment=dto.translator_comment,
                source_url=dto.source_url,
                searchable_text=build_searchable_text(dto.title, dto.raw_transcript),
            )
            .returning(TranslationModel.translation_id)
        )

        try:
            translation_id = await self._session.scalar(stmt)
        except IntegrityError as err:
            self._handle_db_error(err)
        else:
            return TranslationResponseDTO.from_model(model=await self._get_by_id(translation_id))

    async def update_original(
        self,
        comic_id: ComicID,
        dto: TranslationRequestDTO,
    ) -> TranslationResponseDTO:
        stmt = select(TranslationModel.translation_id).where(
            TranslationModel.comic_id == comic_id, TranslationModel.language == Language.EN
        )
        translation_id = await self._session.scalar(stmt)

        return await self.update(translation_id, dto)

    async def update_draft_status(
        self,
        translation_id: TranslationID,
        *,
        new_draft_status: bool,
    ) -> None:
        translation = await self._get_by_id(translation_id, ())
        translation.is_draft = new_draft_status

    async def delete(self, translation_id: TranslationID) -> None:
        stmt = delete(TranslationModel).where(TranslationModel.translation_id == translation_id)
        await self._session.execute(stmt)

    async def get_by_id(self, translation_id: TranslationID) -> TranslationResponseDTO:
        return TranslationResponseDTO.from_model(model=await self._get_by_id(translation_id))

    async def get_by_language(
        self, comic_id: ComicID, language: Language
    ) -> TranslationResponseDTO:
        stmt = select(TranslationModel).where(
            TranslationModel.comic_id == comic_id,
            TranslationModel.language == language,
        )

        translation = (await self._session.scalars(stmt)).unique().one_or_none()

        if not translation:
            raise TranslationNotFoundError

        return TranslationResponseDTO.from_model(translation)

    async def _get_by_id(
        self,
        translation_id: TranslationID,
        options: Sequence[ORMOption] | None = None,
    ) -> TranslationModel:
        if options is None:
            options = (joinedload(TranslationModel.images),)

        translation = await self._get_model_by_id(TranslationModel, translation_id, options=options)

        if not translation:
            raise TranslationNotFoundError

        return translation

    def _handle_db_error(self, err: DBAPIError) -> NoReturn:
        cause = str(err.__cause__)

        if UNIQUE_TRANSLATION_IF_NOT_DRAFT_CONSTRAINT in cause:
            raise TranslationAlreadyExistsError
        if "fk_translations_comic_id_comics" in cause:
            raise ComicNotFoundError

        raise err
