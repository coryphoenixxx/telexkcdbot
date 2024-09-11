from functools import singledispatchmethod
from typing import NoReturn

from sqlalchemy import ColumnElement, and_, delete, false, func, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.orm import contains_eager, joinedload, selectinload

from backend.application.comic.dtos import ComicRequestDTO, ComicResponseDTO, TranslationResponseDTO
from backend.application.comic.exceptions import (
    ComicNotFoundError,
    ComicNumberAlreadyExistsError,
    ExtraComicTitleAlreadyExistsError,
)
from backend.application.comic.interfaces import ComicRepoInterface
from backend.application.common.pagination import (
    ComicFilterParams,
    Order,
    TagParam,
    TotalCount,
)
from backend.application.utils import slugify
from backend.core.value_objects import ComicID, IssueNumber, Language
from backend.infrastructure.database.models import (
    ComicModel,
    TagModel,
    TranslationModel,
)
from backend.infrastructure.database.repositories.base import BaseRepo, RepoError


class ComicRepo(BaseRepo, ComicRepoInterface):
    async def create(self, dto: ComicRequestDTO) -> ComicID:
        try:
            comic_id = await self._session.scalar(
                insert(ComicModel)
                .values(
                    number=dto.number.value if dto.number else None,
                    slug=self._build_slug(dto.number, dto.title),
                    publication_date=dto.publication_date,
                    explain_url=dto.explain_url,
                    click_url=dto.click_url,
                    is_interactive=dto.is_interactive,
                )
                .returning(ComicModel.comic_id)
            )
        except IntegrityError as err:
            self._handle_db_error(dto, err)
        else:
            if comic_id:
                return ComicID(comic_id)
            raise RepoError

    async def update(self, comic_id: ComicID, dto: ComicRequestDTO) -> None:
        stmt = (
            update(ComicModel)
            .where(and_(ComicModel.comic_id == comic_id.value))
            .values(
                number=dto.number.value if dto.number else None,
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
            self._handle_db_error(dto, err)

    async def delete(self, comic_id: ComicID) -> None:
        await self._session.execute(
            delete(ComicModel).where(and_(ComicModel.comic_id == comic_id.value))
        )

    @singledispatchmethod
    async def get_by(self) -> NoReturn:
        raise NotImplementedError

    @get_by.register  # type: ignore[arg-type]
    async def _(self, value: ComicID) -> ComicResponseDTO:
        return await self._get_by(value, and_(ComicModel.comic_id == value.value))

    @get_by.register  # type: ignore[arg-type]
    async def _(self, value: IssueNumber) -> ComicResponseDTO:
        return await self._get_by(value, and_(ComicModel.number == value.value))

    @get_by.register  # type: ignore[arg-type]
    async def _(self, value: str) -> ComicResponseDTO:
        return await self._get_by(value, and_(ComicModel.slug == value))

    async def _get_by(
        self,
        value: ComicID | IssueNumber | str,
        where_clause: ColumnElement[bool],
    ) -> ComicResponseDTO:
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
            raise ComicNotFoundError(value)

        comic.tags = [tag for tag in comic.tags if not tag.is_blacklisted]

        return comic.to_dto()

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

        return TotalCount(total), [c.to_dto() for c in comics]

    async def get_issue_number_by_id(self, comic_id: ComicID) -> IssueNumber | None:
        comic = await self._get_model_by_id(ComicModel, comic_id.value)

        if not comic:
            raise ComicNotFoundError(comic_id)

        if comic.number:
            return IssueNumber(comic.number)
        return None

    async def get_translations(self, comic_id: ComicID) -> list[TranslationResponseDTO]:
        stmt = (
            select(TranslationModel)
            .where(
                and_(TranslationModel.comic_id == comic_id.value),
                TranslationModel.is_draft == false(),
                TranslationModel.language != Language.EN,
            )
            .options(joinedload(TranslationModel.image))
        )

        translations = (await self._session.scalars(stmt)).unique().all()

        return [t.to_dto() for t in translations]

    def _build_slug(self, number: IssueNumber | None, en_title: str) -> str | None:
        return slugify(en_title) if number is None else None

    def _handle_db_error(self, dto: ComicRequestDTO, err: DBAPIError) -> NoReturn:
        cause = str(err.__cause__)

        if dto.number and "uq_comic_number_if_not_extra" in cause:
            raise ComicNumberAlreadyExistsError(dto.number)
        if "uq_comic_title_if_extra" in cause:
            raise ExtraComicTitleAlreadyExistsError(dto.title)

        raise RepoError from err
