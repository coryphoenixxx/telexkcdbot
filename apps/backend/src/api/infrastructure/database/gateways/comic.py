from collections.abc import Sequence
from typing import NoReturn

from shared.my_types import Order
from sqlalchemy import delete, false, func, select, true
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.orm import joinedload, selectinload
from sqlalchemy.orm.interfaces import ORMOption

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
from api.core.value_objects import ComicID, IssueNumber
from api.infrastructure.database.exceptions import GatewayError
from api.infrastructure.database.gateways.base import BaseGateway
from api.infrastructure.database.models import (
    UNIQUE_COMIC_NUMBER_IF_NOT_EXTRA_CONSTRAINT,
    UNIQUE_COMIC_TITLE_IF_NOT_EXTRA_CONSTRAINT,
    ComicModel,
    TagModel,
    TranslationModel,
)
from api.infrastructure.slugger import slugify


class ComicGateway(BaseGateway):
    @property
    def default_load_options(self) -> Sequence[ORMOption]:
        return (
            joinedload(ComicModel.tags),
            joinedload(ComicModel.translations).options(
                joinedload(TranslationModel.images),
            ),
        )

    async def create_base(self, dto: ComicRequestDTO) -> ComicID:
        comic = ComicModel(
            number=dto.number,
            slug=self._build_slug(dto.number, dto.title),
            publication_date=dto.publication_date,
            explain_url=dto.explain_url,
            click_url=dto.click_url,
            is_interactive=dto.is_interactive,
            tags=await self._create_tags(dto.tags),
        )

        self._session.add(comic)

        try:
            await self._session.flush()
        except IntegrityError as err:
            self._handle_db_error(err)
        else:
            return comic.comic_id

    async def update_base(self, comic_id: ComicID, dto: ComicRequestDTO) -> None:
        comic = await self._get_by_id(comic_id, options=(joinedload(ComicModel.tags),))

        comic.number = dto.number
        comic.slug = self._build_slug(dto.number, dto.title)
        comic.publication_date = dto.publication_date
        comic.explain_url = dto.explain_url
        comic.click_url = dto.click_url
        comic.is_interactive = dto.is_interactive
        comic.tags = await self._create_tags(dto.tags)

        try:
            await self._session.flush()
        except IntegrityError as err:
            self._handle_db_error(err)

    async def delete(self, comic_id: ComicID) -> None:
        await self._session.execute(delete(ComicModel).where(ComicModel.comic_id == comic_id))

    async def get_by_id(self, comic_id: ComicID) -> ComicResponseDTO:
        return ComicResponseDTO.from_model(model=await self._get_by_id(comic_id))

    async def get_by_issue_number(self, number: IssueNumber) -> ComicResponseDTO:
        stmt = (
            select(ComicModel)
            .where(ComicModel.number == number)
            .options(*self.default_load_options)
        )

        comic = (await self._session.scalars(stmt)).unique().one_or_none()
        if not comic:
            raise ComicNotFoundError

        return ComicResponseDTO.from_model(comic)

    async def get_by_slug(self, slug: str) -> ComicResponseDTO:
        stmt = select(ComicModel).where(ComicModel.slug == slug).options(*self.default_load_options)

        comic = (await self._session.scalars(stmt)).unique().one_or_none()
        if not comic:
            raise ComicNotFoundError

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
                    joinedload(TranslationModel.images),
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
            .options(joinedload(TranslationModel.images))
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
            .options(joinedload(TranslationModel.images))
        )

        translations = (await self._session.scalars(stmt)).unique().all()

        return [TranslationResponseDTO.from_model(model) for model in translations]

    async def _create_tags(self, tag_names: list[str]) -> list[TagModel]:
        if not tag_names:
            return []

        stmt = (
            insert(TagModel)
            .values([{"name": name} for name in tag_names])
            .on_conflict_do_nothing(constraint="uq_tags_name")
        )

        await self._session.execute(stmt)

        stmt = select(TagModel).where(TagModel.name.in_(tag_names))

        return list((await self._session.scalars(stmt)).all())

    async def _get_by_id(
        self,
        comic_id: ComicID,
        options: Sequence[ORMOption] | None = None,
    ) -> ComicModel:
        if options is None:
            options = self.default_load_options

        comic = await self._get_model_by_id(ComicModel, comic_id, options=options)

        if not comic:
            raise ComicNotFoundError

        return comic

    def _build_slug(self, number: int | None, en_title: str) -> str:
        slug = slugify(en_title)

        if number:
            return f"{number}-{slug}"
        return slug

    def _handle_db_error(self, err: DBAPIError) -> NoReturn:
        cause = str(err.__cause__)

        if UNIQUE_COMIC_NUMBER_IF_NOT_EXTRA_CONSTRAINT in cause:
            raise ComicNumberAlreadyExistsError
        if UNIQUE_COMIC_TITLE_IF_NOT_EXTRA_CONSTRAINT in cause:
            raise ExtraComicTitleAlreadyExistsError

        raise GatewayError from err
