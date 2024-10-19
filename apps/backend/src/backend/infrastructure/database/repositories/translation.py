from typing import NoReturn

from sqlalchemy import delete, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.orm import contains_eager

from backend.application.comic.exceptions import (
    ComicNotFoundError,
    TranslationAlreadyExistsError,
    TranslationNotFoundError,
)
from backend.application.comic.interfaces import TranslationRepoInterface
from backend.application.comic.responses import TranslationResponseData
from backend.domain.entities import (
    NewTranslationEntity,
    TranslationEntity,
)
from backend.domain.value_objects import ComicId, Language
from backend.domain.value_objects.common import TranslationId
from backend.infrastructure.database.mappers import (
    map_translation_entity_to_dict,
    map_translation_model_to_data,
    map_translation_model_to_entity,
)
from backend.infrastructure.database.models import TranslationModel
from backend.infrastructure.database.repositories import BaseRepo, RepoError


class TranslationRepo(BaseRepo, TranslationRepoInterface):
    async def create(self, translation: NewTranslationEntity) -> TranslationId:
        try:
            translation_id: int = await self.session.scalar(  # type: ignore[assignment]
                insert(TranslationModel)
                .values(map_translation_entity_to_dict(translation))
                .returning(TranslationModel.translation_id)
            )
        except IntegrityError as err:
            self._handle_db_error(
                err,
                comic_id=translation.comic_id,
                language=translation.language,
            )
        else:
            return TranslationId(translation_id)

    async def update(self, translation: TranslationEntity) -> None:
        stmt = (
            update(TranslationModel)
            .where(TranslationModel.translation_id == translation.id.value)
            .values(map_translation_entity_to_dict(translation))
        )

        try:
            await self.session.execute(stmt)
        except IntegrityError as err:
            self._handle_db_error(
                err,
                language=translation.language,
            )

    async def delete(self, translation_id: TranslationId) -> None:
        stmt = delete(TranslationModel).where(
            TranslationModel.translation_id == translation_id.value
        )
        await self.session.execute(stmt)

    async def get_by_id(self, translation_id: TranslationId) -> TranslationResponseData:
        stmt = (
            select(TranslationModel)
            .outerjoin(TranslationModel.image)
            .options(contains_eager(TranslationModel.image))
            .where(TranslationModel.translation_id == translation_id.value)
        )

        translation: TranslationModel | None = (
            (await self.session.scalars(stmt)).unique().one_or_none()
        )

        if translation is None:
            raise TranslationNotFoundError(translation_id)

        return map_translation_model_to_data(translation)

    async def load(self, translation_id: TranslationId) -> TranslationEntity:
        translation = await self.session.get(
            TranslationModel,
            translation_id.value,
            with_for_update=True,
        )

        if translation is None:
            raise TranslationNotFoundError(translation_id)

        return map_translation_model_to_entity(translation)

    def _handle_db_error(
        self,
        err: DBAPIError,
        *,
        comic_id: ComicId | None = None,
        language: Language | None = None,
    ) -> NoReturn:
        cause = str(err.__cause__)

        if language and "uq_translation_if_not_draft" in cause:
            raise TranslationAlreadyExistsError(language)
        if comic_id and "fk_translations_comic_id_comics" in cause:
            raise ComicNotFoundError(comic_id)

        raise RepoError from err
