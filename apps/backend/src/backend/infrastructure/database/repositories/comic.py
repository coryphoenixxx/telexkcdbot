from dataclasses import dataclass
from functools import singledispatchmethod
from typing import NoReturn

from sqlalchemy import BinaryExpression, and_, delete, false, func, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.orm import contains_eager, joinedload, selectinload

from backend.application.dtos import ComicRequestDTO, ComicResponseDTO, TranslationResponseDTO
from backend.core.exceptions.base import BaseAppError
from backend.core.value_objects import ComicID, IssueNumber, Language
from backend.infrastructure.database.dtos import ComicFilterParams, Order, TagParam, TotalCount
from backend.infrastructure.database.models import (
    ComicModel,
    TagModel,
    TranslationModel,
)
from backend.infrastructure.database.repositories.base import BaseRepo, RepoError
from backend.infrastructure.utils import slugify

ComicGetByType = ComicID | IssueNumber | str


@dataclass(slots=True, eq=False)
class ComicNotFoundError(BaseAppError):
    value: int | str

    @property
    def message(self) -> str:
        match self.value:
            case ComicID():
                return f"A comic (id={self.value}) not found."
            case IssueNumber():
                return f"A comic (number={self.value}) not found."
            case str():
                return f"A comic (slug=`{self.value}`) not found."
            case _:
                raise ValueError("Invalid type.")


@dataclass(slots=True, eq=False)
class ComicNumberAlreadyExistsError(BaseAppError):
    number: int

    @property
    def message(self) -> str:
        return f"A comic with this issue number ({self.number}) already exists."


@dataclass(slots=True, eq=False)
class ExtraComicTitleAlreadyExistsError(BaseAppError):
    title: str

    @property
    def message(self) -> str:
        return f"An extra comic with this title (`{self.title}`) already exists."


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
            self._handle_db_error(dto, err)
        else:
            return ComicID(comic_id)

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
            self._handle_db_error(dto, err)

    async def delete(self, comic_id: ComicID) -> None:
        await self._session.execute(delete(ComicModel).where(ComicModel.comic_id == comic_id))

    @singledispatchmethod
    async def get_by(self) -> NoReturn:
        raise NotImplementedError

    @get_by.register
    async def _(self, value: ComicID) -> ComicResponseDTO:
        return await self._get_by(value, and_(ComicModel.comic_id == value))

    @get_by.register
    async def _(self, value: IssueNumber) -> ComicResponseDTO:
        return await self._get_by(value, and_(ComicModel.number == value))

    @get_by.register
    async def _(self, value: str) -> ComicResponseDTO:
        return await self._get_by(value, and_(ComicModel.slug == value))

    async def _get_by(
        self,
        value: ComicGetByType,
        where_clause: BinaryExpression[bool],
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

        if not comic:  # TODO: handle in application layer?
            raise ComicNotFoundError(value)

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

    async def get_issue_number_by_id(self, comic_id: ComicID) -> IssueNumber | None:
        comic = await self._get_model_by_id(ComicModel, comic_id)

        if not comic:
            raise ComicNotFoundError(comic_id)

        if comic.number:
            return IssueNumber(comic.number)
        return None

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

    def _build_slug(self, number: int | None, en_title: str) -> str | None:
        return slugify(en_title) if number is None else None

    def _handle_db_error(self, dto: ComicRequestDTO, err: DBAPIError) -> NoReturn:
        cause = str(err.__cause__)

        if "uq_comic_number_if_not_extra" in cause:
            raise ComicNumberAlreadyExistsError(dto.number)
        if "uq_comic_title_if_extra" in cause:
            raise ExtraComicTitleAlreadyExistsError(dto.title)

        raise RepoError from err
