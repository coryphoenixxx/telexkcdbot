from collections.abc import Iterable

from slugify import slugify
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from .dtos.requests import ComicRequestDTO
from .dtos.responses import ComicResponseDTO, ComicResponseWithTranslationsDTO
from .exceptions import (
    ComicByIssueNumberNotFoundError,
    ComicIssueNumberUniqueError,
    ComicNotFoundError,
    ExtraComicBySlugNotFoundError,
)
from .models import ComicModel, TagModel
from .types import ComicID


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
                issue_number=dto.issue_number,
                slug=slugify(en_title, separator="_"),
                publication_date=dto.publication_date,
                xkcd_url=dto.xkcd_url,
                reddit_url=dto.reddit_url,
                explain_url=dto.explain_url,
                link_on_click=dto.link_on_click,
                is_interactive=dto.is_interactive,
                tags=tags,
                translations=[],
            )

            self._session.add(comic)
            await self._session.flush()
        except IntegrityError as err:
            self._handle_integrity_error(err=err, dto=dto)
        else:
            return comic.to_dto(with_translations=True)

    async def update(
        self,
        comic_id: ComicID,
        comic_dto: ComicRequestDTO,
    ) -> ComicResponseDTO:
        comic: ComicModel = await self._get_by_id(comic_id)

        comic.issue_number = comic_dto.issue_number
        comic.publication_date = comic_dto.publication_date
        comic.xkcd_url = comic_dto.xkcd_url
        comic.reddit_url = comic_dto.reddit_url
        comic.explain_url = comic_dto.explain_url
        comic.link_on_click = comic_dto.link_on_click
        comic.is_interactive = comic_dto.is_interactive
        comic.tags = await self._create_tags(comic_dto.tags)

        return comic.to_dto()

    async def get_by_id_with_translations(
        self,
        comic_id: ComicID,
    ) -> ComicResponseWithTranslationsDTO:
        stmt = (
            select(ComicModel)
            .options(joinedload(ComicModel.translations))
            .where(ComicModel.id == comic_id)
        )

        comic = (await self._session.scalars(stmt)).unique().one_or_none()

        if not comic:
            raise ComicNotFoundError(comic_id=comic_id)

        return comic.to_dto(with_translations=True)

    async def get_by_issue_number(self, issue_number: int) -> ComicResponseWithTranslationsDTO:
        stmt = (
            select(ComicModel)
            .options(joinedload(ComicModel.translations))
            .where(ComicModel.issue_number == issue_number)
        )

        comic = (await self._session.scalars(stmt)).unique().one_or_none()

        if not comic:
            raise ComicByIssueNumberNotFoundError(issue_number=issue_number)

        return comic.to_dto(with_translations=True)

    async def get_by_slug(self, slug: str) -> ComicResponseWithTranslationsDTO:
        stmt = (
            select(ComicModel)
            .options(joinedload(ComicModel.translations))
            .where(ComicModel.slug == slug)
            .where(ComicModel.issue_number.is_(None))
        )

        comic = (await self._session.scalars(stmt)).unique().one_or_none()

        if not comic:
            raise ExtraComicBySlugNotFoundError(slug=slug)

        return comic.to_dto(with_translations=True)

    async def get_all(self) -> list[ComicResponseWithTranslationsDTO]:
        stmt = select(ComicModel).options(joinedload(ComicModel.translations))

        comics = (await self._session.scalars(stmt)).unique().all()

        return [comic.to_dto(with_translations=True) for comic in comics]

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

    async def _get_by_id(self, comic_id: ComicID) -> ComicModel:
        stmt = select(ComicModel).where(ComicModel.id == comic_id)

        comic = (await self._session.scalars(stmt)).unique().one_or_none()

        if not comic:
            raise ComicNotFoundError(comic_id=comic_id)

        return comic

    def _handle_integrity_error(self, err: IntegrityError, dto: ComicRequestDTO):
        constraint = err.__cause__.__cause__.constraint_name
        if constraint == "uq_issue_number_if_not_none":
            raise ComicIssueNumberUniqueError(issue_number=dto.issue_number)
        raise err
