from collections.abc import Iterable
from typing import Sequence

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import noload

from api.core.utils import slugify
from .dtos.request import ComicRequestDTO
from .dtos.response import ComicResponseDTO, ComicResponseWithTranslationsDTO
from .exceptions import (
    ComicByIssueNumberNotFoundError,
    ComicIssueNumberUniqueError,
    ComicNotFoundError,
    ExtraComicByTitleNotFoundError,
    ExtraComicSlugUniqueError,
)
from .models import ComicModel, TagModel
from .types import ComicID, IssueNumber


class ComicRepo:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(
        self,
        dto: ComicRequestDTO,
        en_title: str,
    ) -> ComicResponseWithTranslationsDTO:
        try:
            tags = await self._create_tags(dto.tags)

            comic = ComicModel(
                number=dto.number,
                slug=slugify(en_title),
                publication_date=dto.publication_date,
                xkcd_url=dto.xkcd_url,
                explain_url=dto.explain_url,
                link_on_click=dto.link_on_click,
                is_interactive=dto.is_interactive,
                tags=tags,
                translations=[],
            )

            self._session.add(comic)
            await self._session.flush()
        except IntegrityError as err:
            self._handle_integrity_error(err=err, dto=dto, en_title=en_title)
        else:
            return ComicResponseWithTranslationsDTO.from_model(model=comic)

    async def update(
        self,
        comic_id: ComicID,
        dto: ComicRequestDTO,
    ) -> ComicResponseDTO:
        comic: ComicModel = await self._get_by_id(comic_id, with_translations=False)

        try:
            comic.number = dto.number
            comic.publication_date = dto.publication_date
            comic.xkcd_url = dto.xkcd_url
            comic.explain_url = dto.explain_url
            comic.link_on_click = dto.link_on_click
            comic.is_interactive = dto.is_interactive
            comic.tags = await self._create_tags(dto.tags)

            await self._session.flush()
        except IntegrityError as err:
            self._handle_integrity_error(err=err, dto=dto)
        else:
            return ComicResponseDTO.from_model(model=comic)

    async def get_by_id(self, comic_id: ComicID) -> ComicResponseWithTranslationsDTO:
        comic: ComicModel = await self._get_by_id(comic_id)
        return ComicResponseWithTranslationsDTO.from_model(model=comic)

    async def get_by_number(self, number: IssueNumber) -> ComicResponseWithTranslationsDTO:
        stmt = select(ComicModel).where(ComicModel.number == number)

        comic: ComicModel | None = (await self._session.scalars(stmt)).unique().one_or_none()

        if not comic:
            raise ComicByIssueNumberNotFoundError(number=number)

        return ComicResponseWithTranslationsDTO.from_model(model=comic)

    async def get_extra_by_title(self, title: str) -> ComicResponseWithTranslationsDTO:
        stmt = (
            select(ComicModel)
            .where(ComicModel.slug == slugify(title))
            .where(ComicModel.number.is_(None))
        )

        comic: ComicModel | None = (await self._session.scalars(stmt)).unique().one_or_none()

        if not comic:
            raise ExtraComicByTitleNotFoundError(title=title)

        return ComicResponseWithTranslationsDTO.from_model(model=comic)

    async def get_list(self) -> list[ComicResponseWithTranslationsDTO]:
        comics: Sequence[ComicModel] = (
            (await self._session.scalars(select(ComicModel))).unique().all()
        )

        return [ComicResponseWithTranslationsDTO.from_model(model=comic) for comic in comics]

    async def delete(self, comic_id: ComicID):
        stmt = (
            delete(ComicModel)
            .options(noload(ComicModel.tags), noload(ComicModel.translations))
            .where(ComicModel.id == comic_id)
            .returning(ComicModel)
        )

        comic = (await self._session.scalars(stmt)).one_or_none()

        if not comic:
            raise ComicNotFoundError(comic_id=comic_id)

    async def _create_tags(self, tag_names: list[str]) -> Iterable[TagModel]:
        if not tag_names:
            return []

        tags = (TagModel(name=tag_name) for tag_name in tag_names)

        stmt = (
            insert(TagModel)
            .values([{"name": tag.name} for tag in tags])
            .on_conflict_do_nothing(
                constraint="uq_tags_name",
            )
        )

        await self._session.execute(stmt)

        stmt = select(TagModel).where(TagModel.name.in_(tag_names))

        return (await self._session.scalars(stmt)).all()

    async def _get_by_id(self, comic_id: ComicID, with_translations: bool = True) -> ComicModel:
        stmt = select(ComicModel).where(ComicModel.id == comic_id)
        if not with_translations:
            stmt = stmt.options(noload(ComicModel.translations))

        comic: ComicModel = (await self._session.scalars(stmt)).unique().one_or_none()

        if not comic:
            raise ComicNotFoundError(comic_id=comic_id)

        return comic

    @staticmethod
    def _handle_integrity_error(
        err: IntegrityError,
        dto: ComicRequestDTO,
        en_title: str | None = None,
    ):
        constraint = err.__cause__.__cause__.constraint_name
        if constraint == "uq_number_if_not_extra":
            raise ComicIssueNumberUniqueError(number=dto.number)
        if en_title and constraint == "uq_title_if_extra":
            raise ExtraComicSlugUniqueError(title=en_title)
        raise err
