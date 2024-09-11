import re
from collections.abc import Sequence
from html import unescape
from typing import NoReturn

from sqlalchemy import and_, delete, false, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.orm import joinedload
from sqlalchemy.orm.interfaces import ORMOption

from backend.application.comic.dtos import TranslationRequestDTO, TranslationResponseDTO
from backend.application.comic.exceptions import (
    ComicNotFoundError,
    TranslationAlreadyExistsError,
    TranslationNotFoundError,
)
from backend.application.comic.interfaces import TranslationRepoInterface
from backend.core.value_objects import ComicID, Language, TranslationID
from backend.infrastructure.database.models import TranslationModel
from backend.infrastructure.database.repositories import BaseRepo, RepoError

SQUARE_BRACKETS_PATTERN = re.compile(r"\[.*?]")
HTML_TAG_PATTERN = re.compile(r"<.*?>")
SPEAKER_PATTERN = re.compile(r"^[\[\w -\]]{3,20}: ", re.UNICODE | re.MULTILINE)
SEPARATE_NUMBER_PATTERN = re.compile(r"\s[0-9]+\s")
REPEATED_EMPTIES_PATTERN = re.compile(r"\s\s+")
SINGLE_CHARACTER_PATTERN = re.compile(r"\b.\b")
PUNCTUATION_PATTERN = re.compile(r"[.:;!?,/\"\']")


def build_searchable_text(title: str, raw_transcript: str) -> str:
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


class TranslationRepo(BaseRepo, TranslationRepoInterface):
    async def create(
        self,
        comic_id: ComicID,
        dto: TranslationRequestDTO,
    ) -> TranslationResponseDTO:
        stmt = (
            insert(TranslationModel)
            .values(
                comic_id=comic_id.value,
                title=dto.title,
                language=dto.language,
                tooltip=dto.tooltip,
                raw_transcript=dto.raw_transcript,
                translator_comment=dto.translator_comment,
                source_url=dto.source_url,
                is_draft=dto.is_draft,
                searchable_text=(
                    build_searchable_text(
                        dto.title,
                        dto.raw_transcript,
                    )
                    if dto.is_draft is False
                    else ""
                ),
            )
            .returning(TranslationModel.translation_id)
        )

        try:
            translation_id = await self._session.scalar(stmt)
            if translation_id is None:
                raise RepoError
        except IntegrityError as err:
            self._handle_db_error(comic_id, dto, err)
        else:
            translation = await self._get_by_id(TranslationID(translation_id))
            return translation.to_dto()

    async def update(
        self,
        translation_id: TranslationID,
        dto: TranslationRequestDTO,
    ) -> TranslationResponseDTO:
        stmt = (
            update(TranslationModel)
            .where(and_(TranslationModel.translation_id == translation_id.value))
            .values(
                title=dto.title,
                language=dto.language,
                tooltip=dto.tooltip,
                raw_transcript=dto.raw_transcript,
                translator_comment=dto.translator_comment,
                source_url=dto.source_url,
                searchable_text=(
                    build_searchable_text(
                        dto.title,
                        dto.raw_transcript,
                    )
                    if dto.is_draft is False
                    else ""
                ),
            )
            .returning(TranslationModel.translation_id)
        )

        try:
            db_translation_id = await self._session.scalar(stmt)
            if db_translation_id is None:
                raise RepoError
        except IntegrityError as err:
            self._handle_db_error(None, dto, err)
        else:
            translation = await self._get_by_id(TranslationID(db_translation_id))
            return translation.to_dto()

    async def update_original(
        self,
        comic_id: ComicID,
        dto: TranslationRequestDTO,
    ) -> TranslationResponseDTO:
        stmt = select(TranslationModel.translation_id).where(
            and_(TranslationModel.comic_id == comic_id.value),
            TranslationModel.language == Language.EN,
        )
        translation_id = await self._session.scalar(stmt)

        if translation_id is None:
            raise RepoError

        return await self.update(TranslationID(translation_id), dto)

    async def update_draft_status(
        self,
        translation_id: TranslationID,
        new_draft_status: bool,
    ) -> None:
        translation = await self._get_by_id(translation_id)
        translation.is_draft = new_draft_status
        await self._session.flush()

    async def delete(self, translation_id: TranslationID) -> None:
        stmt = delete(TranslationModel).where(
            and_(TranslationModel.translation_id == translation_id.value)
        )
        await self._session.execute(stmt)

    async def get_by_id(self, translation_id: TranslationID) -> TranslationResponseDTO:
        translation = await self._get_by_id(translation_id)
        return translation.to_dto()

    async def get_by_language(
        self,
        comic_id: ComicID,
        language: Language,
    ) -> TranslationResponseDTO | None:
        stmt = (
            select(TranslationModel)
            .options(joinedload(TranslationModel.image))
            .where(
                and_(
                    TranslationModel.comic_id == comic_id.value,
                    TranslationModel.language == language,
                    TranslationModel.is_draft == false(),
                ),
            )
        )

        translation = (await self._session.scalars(stmt)).unique().one_or_none()

        if translation:
            return translation.to_dto()
        return None

    async def _get_by_id(
        self,
        translation_id: TranslationID,
        options: Sequence[ORMOption] | None = None,
    ) -> TranslationModel:
        if options is None:
            options = (joinedload(TranslationModel.image),)

        translation = await self._get_model_by_id(
            TranslationModel,
            translation_id.value,
            options=options,
        )

        if not translation:
            raise TranslationNotFoundError(translation_id)

        return translation

    def _handle_db_error(
        self,
        comic_id: ComicID | None,
        dto: TranslationRequestDTO,
        err: DBAPIError,
    ) -> NoReturn:
        cause = str(err.__cause__)

        if "uq_translation_if_not_draft" in cause:
            raise TranslationAlreadyExistsError(dto.language)
        if comic_id and "fk_translations_comic_id_comics" in cause:
            raise ComicNotFoundError(comic_id)

        raise RepoError from err
