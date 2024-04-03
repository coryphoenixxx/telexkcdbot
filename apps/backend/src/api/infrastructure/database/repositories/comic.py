from collections.abc import Iterable, Sequence

from shared.types import LanguageCode
from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import noload

from api.application.dtos.requests.comic import ComicRequestDTO
from api.application.dtos.responses.comic import ComicResponseDTO, ComicResponseWTranslationsDTO
from api.application.exceptions.comic import (
    ComicByIDNotFoundError,
    ComicByIssueNumberNotFoundError,
    ComicBySlugNotFoundError,
    ComicNumberAlreadyExistsError,
    ExtraComicTitleAlreadyExistsError,
)
from api.application.types import ComicID, IssueNumber
from api.infrastructure.database.models import TranslationModel
from api.infrastructure.database.models.comic import ComicModel, TagModel
from api.infrastructure.database.repositories.base import BaseRepo
from api.infrastructure.database.repositories.mixins import GetImagesMixin
from api.infrastructure.database.types import ComicFilterParams, Order
from api.infrastructure.database.utils import build_searchable_text
from api.utils import slugify


class ComicRepo(BaseRepo, GetImagesMixin):
    async def create(
        self,
        dto: ComicRequestDTO,
    ) -> ComicResponseDTO:
        tags = await self._create_tags(dto.tags)

        comic = ComicModel(
            number=dto.number,
            slug=self._build_slug(dto.number, dto.title),
            publication_date=dto.publication_date,
            xkcd_url=dto.xkcd_url,
            explain_url=dto.explain_url,
            link_on_click=dto.link_on_click,
            is_interactive=dto.is_interactive,
            tags=tags,
            translations=[
                TranslationModel(
                    title=dto.title,
                    language=LanguageCode.EN,
                    tooltip=dto.tooltip,
                    transcript_raw=dto.transcript_raw,
                    translator_comment="",
                    source_link=dto.xkcd_url,
                    images=await self._get_images(self._session, dto.image_ids),
                    is_draft=False,
                    searchable_text=build_searchable_text(dto.title, dto.transcript_raw),
                    drafts=[],
                ),
            ],
        )

        self._session.add(comic)

        try:
            await self._session.flush()
        except IntegrityError as err:
            self._handle_db_error(err, dto)
        else:
            await self._session.refresh(comic, attribute_names=["en_translation"])
            return ComicResponseDTO.from_model(model=comic)

    async def update(
        self,
        comic_id: ComicID,
        dto: ComicRequestDTO,
    ) -> ComicResponseDTO:
        comic: ComicModel = await self._get_by_id(comic_id)
        print(comic)

        tags = await self._create_tags(dto.tags)

        comic.number = dto.number
        comic.slug = self._build_slug(dto.number, dto.title)
        comic.publication_date = dto.publication_date
        comic.xkcd_url = dto.xkcd_url
        comic.explain_url = dto.explain_url
        comic.link_on_click = dto.link_on_click
        comic.is_interactive = dto.is_interactive
        comic.tags = tags

        comic.en_translation.title = dto.title
        comic.en_translation.tooltip = dto.tooltip
        comic.en_translation.transcript_raw = dto.transcript_raw
        comic.en_translation.images = await self._get_images(self._session, dto.image_ids)

        try:
            await self._session.flush()
        except IntegrityError as err:
            self._handle_db_error(err, dto)
        else:
            return ComicResponseDTO.from_model(model=comic)

    async def delete(self, comic_id: ComicID) -> None:
        stmt = (
            delete(ComicModel)
            .options(noload(ComicModel.tags), noload(ComicModel.translations))
            .where(ComicModel.comic_id == comic_id)
            .returning(ComicModel)
        )

        comic: ComicModel | None = (await self._session.scalars(stmt)).unique().one_or_none()

        if not comic:
            raise ComicByIDNotFoundError(comic_id=comic_id)

    async def get_by_id(self, comic_id: ComicID) -> ComicResponseWTranslationsDTO:
        comic: ComicModel = await self._get_by_id(comic_id)

        return ComicResponseWTranslationsDTO.from_model(model=comic)

    async def get_by_issue_number(self, number: IssueNumber) -> ComicResponseWTranslationsDTO:
        stmt = select(ComicModel).where(ComicModel.number == number)

        comic: ComicModel | None = (await self._session.scalars(stmt)).unique().one_or_none()

        if not comic:
            raise ComicByIssueNumberNotFoundError(number=number)

        return ComicResponseWTranslationsDTO.from_model(model=comic)

    async def get_by_slug(self, slug: str) -> ComicResponseWTranslationsDTO:
        stmt = select(ComicModel).where(ComicModel.slug == slug).options()

        comic: ComicModel | None = (await self._session.scalars(stmt)).unique().one_or_none()

        if not comic:
            raise ComicBySlugNotFoundError(slug=slug)

        return ComicResponseWTranslationsDTO.from_model(model=comic)

    async def get_list(
        self, query_params: ComicFilterParams
    ) -> list[ComicResponseWTranslationsDTO]:
        stmt = select(ComicModel)

        if not query_params.order or query_params.order == Order.ASC:
            stmt = stmt.order_by(ComicModel.number.asc())
        else:
            stmt = stmt.order_by(ComicModel.number.desc())

        if query_params.date_range.start:
            stmt = stmt.where(ComicModel.publication_date >= query_params.date_range.start)
        if query_params.date_range.end:
            stmt = stmt.where(ComicModel.publication_date <= query_params.date_range.end)

        stmt = stmt.limit(query_params.limit).offset(query_params.offset)

        comics: Sequence[ComicModel] = (await self._session.scalars(stmt)).unique().all()

        return [ComicResponseWTranslationsDTO.from_model(model=comic) for comic in comics]

    async def _create_tags(self, tag_names: list[str]) -> Iterable[TagModel]:
        if not tag_names:
            return []

        stmt = (
            insert(TagModel)
            .values([{"name": name} for name in tag_names])
            .on_conflict_do_nothing(constraint="uq_tags_name")
        )

        await self._session.execute(stmt)

        stmt = select(TagModel).where(TagModel.name.in_(tag_names))

        return (await self._session.scalars(stmt)).all()

    async def _get_by_id(self, comic_id: ComicID) -> ComicModel:
        comic = await self._session.get(ComicModel, comic_id)

        if not comic:
            raise ComicByIDNotFoundError(comic_id=comic_id)

        return comic

    def _build_slug(self, number: int | None, en_title: str) -> str:
        slug = slugify(en_title)
        if number:
            return f"{number}-{slug}"
        return slug

    def _handle_db_error(
        self,
        err: IntegrityError,
        dto: ComicRequestDTO,
    ):
        constraint = err.__cause__.__cause__.constraint_name
        if constraint == "uq_number_if_not_extra":
            raise ComicNumberAlreadyExistsError(number=dto.number)
        if constraint == "uq_title_if_extra":
            raise ExtraComicTitleAlreadyExistsError(title=dto.title)
