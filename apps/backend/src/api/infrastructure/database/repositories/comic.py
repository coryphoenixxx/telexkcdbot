from enum import StrEnum, auto
from typing import NoReturn

from shared.my_types import Order
from sqlalchemy import delete, false, func, select, true, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.orm import contains_eager, joinedload, selectinload

from api.application.dtos.common import (
    ComicFilterParams,
    Language,
    TagParam,
    TotalCount,
)
from api.application.dtos.requests import ComicRequestDTO
from api.application.dtos.responses import (
    ComicResponseDTO,
    TranslationResponseDTO,
)
from api.core.exceptions import (
    ComicNotFoundError,
    ComicNumberAlreadyExistsError,
    ExtraComicTitleAlreadyExistsError,
)
from api.core.utils import slugify
from api.core.value_objects import ComicID, IssueNumber
from api.infrastructure.database.exceptions import RepoError
from api.infrastructure.database.models import (
    UNIQUE_COMIC_NUMBER_IF_NOT_EXTRA_CONSTRAINT,
    UNIQUE_COMIC_TITLE_IF_NOT_EXTRA_CONSTRAINT,
    ComicModel,
    TagModel,
    TranslationModel,
)
from api.infrastructure.database.repositories.base import BaseRepo


class ComicGetByCriteria(StrEnum):
    ID = auto()
    NUMBER = auto()
    SLUG = auto()


class ComicRepo(BaseRepo):
    async def create_base(self, dto: ComicRequestDTO) -> ComicID:
        try:
            comic_id = await self._session.scalar(
                insert(ComicModel)
                .values(
                    number=dto.number,
                    slug=self._build_slug(dto.number, dto.title),
                    publication_date=dto.publication_date,
                    explain_url=dto.explain_url,
                    click_url=dto.click_url,
                    is_interactive=dto.is_interactive,
                )
                .returning(ComicModel.comic_id)
            )
        except IntegrityError as err:
            self._handle_db_error(err)
        else:
            return comic_id

    async def update_base(self, comic_id: ComicID, dto: ComicRequestDTO) -> None:
        stmt = (
            update(ComicModel)
            .where(ComicModel.comic_id == comic_id)
            .values(
                number=dto.number,
                slug=self._build_slug(dto.number, dto.title),
                publication_date=dto.publication_date,
                explain_url=dto.explain_url,
                click_url=dto.click_url,
                is_interactive=dto.is_interactive,
            )
        )

        try:
            await self._session.execute(stmt)
        except IntegrityError as err:
            self._handle_db_error(err)

    async def delete(self, comic_id: ComicID) -> None:
        await self._session.execute(delete(ComicModel).where(ComicModel.comic_id == comic_id))

    async def get_by_id(self, comic_id: ComicID) -> ComicResponseDTO:
        return await self._get_by(
            criteria=ComicGetByCriteria.ID,
            value=comic_id,
        )

    async def get_by_issue_number(self, number: IssueNumber) -> ComicResponseDTO:
        return await self._get_by(
            criteria=ComicGetByCriteria.NUMBER,
            value=number,
        )

    async def get_by_slug(self, slug: str) -> ComicResponseDTO:
        return await self._get_by(
            criteria=ComicGetByCriteria.SLUG,
            value=slug,
        )

    async def _get_by(
        self,
        criteria: ComicGetByCriteria,
        value: ComicID | IssueNumber | str,
    ) -> ComicResponseDTO:
        match criteria:
            case criteria.ID:
                where_clause = ComicModel.comic_id == value
            case criteria.NUMBER:
                where_clause = ComicModel.number == value
            case criteria.SLUG:
                where_clause = ComicModel.slug == value
            case _:
                raise RepoError

        stmt = (
            select(ComicModel)
            .outerjoin(ComicModel.tags)
            .join(ComicModel.translations)
            .options(
                contains_eager(ComicModel.tags),
                contains_eager(ComicModel.translations).options(
                    joinedload(TranslationModel.image),
                ),
            )
            .where(
                where_clause,
                TranslationModel.is_draft == false(),
            )
        )

        comic = (await self._session.scalars(stmt)).unique().one_or_none()

        if not comic:
            raise ComicNotFoundError

        comic.tags = [tag for tag in comic.tags if not tag.is_blacklisted]

        return ComicResponseDTO.from_model(comic)

    async def get_list(
        self,
        filter_params: ComicFilterParams,
    ) -> tuple[TotalCount, list[ComicResponseDTO]]:
        stmt = select(ComicModel, func.count(ComicModel.comic_id).over().label("total"))

        if filter_params.q:
            subq = select(TranslationModel.comic_id).where(
                TranslationModel.searchable_text.op("&@")(filter_params.q),
            )
            stmt = stmt.where(ComicModel.comic_id.in_(subq))

        if filter_params.date_range:
            if filter_params.date_range.start:
                stmt = stmt.where(ComicModel.publication_date >= filter_params.date_range.start)
            if filter_params.date_range.end:
                stmt = stmt.where(ComicModel.publication_date <= filter_params.date_range.end)

        if filter_params.tags:
            stmt = stmt.outerjoin(ComicModel.tags).where(TagModel.name.in_(filter_params.tags))
            if filter_params.tag_param == TagParam.AND and len(filter_params.tags) > 1:
                stmt = stmt.group_by(ComicModel.comic_id).having(
                    func.count(TagModel.tag_id) == len(filter_params.tags),
                )

        if not filter_params.order or filter_params.order == Order.ASC:
            stmt = stmt.order_by(ComicModel.number.asc())
        else:
            stmt = stmt.order_by(ComicModel.number.desc())

        stmt = (
            stmt.limit(filter_params.limit)
            .offset(filter_params.offset)
            .options(
                selectinload(ComicModel.tags),
                selectinload(ComicModel.translations).options(
                    joinedload(TranslationModel.image),
                ),
            )
        )

        total, comics = 0, []
        if result := (await self._session.execute(stmt)).unique().all():
            total, comics = result[0][1], [r[0] for r in result]

        return total, [ComicResponseDTO.from_model(comic) for comic in comics]

    async def get_translations(self, comic_id: ComicID) -> list[TranslationResponseDTO]:
        stmt = (
            select(TranslationModel)
            .where(
                TranslationModel.comic_id == comic_id,
                TranslationModel.is_draft == false(),
                TranslationModel.language != Language.EN,
            )
            .options(joinedload(TranslationModel.image))
        )

        translations = (await self._session.scalars(stmt)).unique().all()

        return [TranslationResponseDTO.from_model(model) for model in translations]

    async def get_translation_drafts(self, comic_id: ComicID) -> list[TranslationResponseDTO]:
        stmt = (
            select(TranslationModel)
            .where(
                TranslationModel.comic_id == comic_id,
                TranslationModel.is_draft == true(),
                TranslationModel.language != Language.EN,
            )
            .options(joinedload(TranslationModel.image))
        )

        translations = (await self._session.scalars(stmt)).unique().all()

        return [TranslationResponseDTO.from_model(model) for model in translations]

    def _build_slug(self, number: int | None, en_title: str) -> str | None:
        return slugify(en_title) if number is None else None

    def _handle_db_error(self, err: DBAPIError) -> NoReturn:
        cause = str(err.__cause__)

        if UNIQUE_COMIC_NUMBER_IF_NOT_EXTRA_CONSTRAINT in cause:
            raise ComicNumberAlreadyExistsError
        if UNIQUE_COMIC_TITLE_IF_NOT_EXTRA_CONSTRAINT in cause:
            raise ExtraComicTitleAlreadyExistsError

        raise RepoError from err
