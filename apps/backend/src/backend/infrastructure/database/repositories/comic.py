import re
from collections.abc import Sequence
from datetime import date
from functools import singledispatchmethod
from typing import NoReturn

from sqlalchemy import (
    ColumnElement,
    Result,
    and_,
    delete,
    exists,
    false,
    func,
    select,
    update,
)
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.orm import contains_eager

from backend.application.comic.exceptions import (
    ComicNotFoundError,
    ComicNumberAlreadyExistsError,
    ExtraComicTitleAlreadyExistsError,
    TagNotFoundError,
)
from backend.application.comic.filters import ComicFilters, TagCombination
from backend.application.comic.interfaces import ComicRepoInterface
from backend.application.comic.responses import (
    ComicCompactResponseData,
    ComicResponseData,
    TranslationResponseData,
)
from backend.application.common.pagination import (
    Pagination,
    SortOrder,
)
from backend.domain.entities import ComicEntity, ImageLinkType, NewComicEntity, TranslationStatus
from backend.domain.value_objects import (
    ComicId,
    IssueNumber,
    Language,
    TagId,
)
from backend.domain.value_objects.common import TranslationId
from backend.infrastructure.database.mappers import (
    map_comic_model_to_data,
    map_comic_model_to_entity,
    map_row_to_compact_data,
    map_translation_model_to_data,
)
from backend.infrastructure.database.models import (
    ComicModel,
    ComicTagAssociation,
    ImageModel,
    TagModel,
    TranslationModel,
)
from backend.infrastructure.database.repositories.base import BaseRepo, RepoError

ComicCompactRow = tuple[int, int, date, str, str | None, str | None]

TAG_ID_PATTERN = re.compile(r"Key \(tag_id\)=\((\d+)\)")


class ComicRepo(BaseRepo, ComicRepoInterface):
    async def create(self, new_comic: NewComicEntity) -> tuple[ComicId, TranslationId]:
        try:
            comic_id: int = await self.session.scalar(  # type: ignore[assignment]
                insert(ComicModel)
                .values(
                    number=new_comic.number.value if new_comic.number else None,
                    slug=new_comic.slug,
                    publication_date=new_comic.publication_date,
                    explain_url=new_comic.explain_url,
                    click_url=new_comic.click_url,
                    is_interactive=new_comic.is_interactive,
                )
                .returning(ComicModel.comic_id)
            )

            translation_id: int = await self.session.scalar(  # type: ignore[assignment]
                insert(TranslationModel)
                .values(
                    comic_id=comic_id,
                    title=new_comic.title.value,
                    language=Language.EN,
                    tooltip=new_comic.tooltip,
                    transcript=new_comic.transcript,
                    source_url=new_comic.xkcd_url,
                    status=TranslationStatus.PUBLISHED,
                    searchable_text=new_comic.searchable_text,
                )
                .returning(TranslationModel.translation_id)
            )
        except IntegrityError as err:
            self._handle_db_error(err, entity=new_comic)
        else:
            return ComicId(comic_id), TranslationId(translation_id)

    async def update(self, comic: ComicEntity) -> None:
        try:
            await self.session.execute(
                update(ComicModel)
                .where(ComicModel.comic_id == comic.id.value)
                .values(
                    number=comic.number.value if comic.number else None,
                    slug=comic.slug,
                    publication_date=comic.publication_date,
                    explain_url=comic.explain_url,
                    click_url=comic.click_url,
                    is_interactive=comic.is_interactive,
                )
            )

            await self.session.execute(
                update(TranslationModel)
                .where(TranslationModel.translation_id == comic.original_translation_id.value)
                .values(
                    title=comic.title.value,
                    tooltip=comic.tooltip,
                    transcript=comic.transcript,
                    source_url=comic.xkcd_url,
                    searchable_text=comic.searchable_text,
                )
            )
        except IntegrityError as err:
            self._handle_db_error(err, entity=comic)

    async def delete(self, comic_id: ComicId) -> None:
        await self.session.execute(
            delete(ComicModel).where(and_(ComicModel.comic_id == comic_id.value))
        )

    @singledispatchmethod
    async def get_by(self) -> NoReturn:
        raise NotImplementedError

    @get_by.register  # type: ignore[arg-type]
    async def _(self, comic_id: ComicId) -> ComicResponseData:
        return await self._get_by(comic_id, ComicModel.comic_id == comic_id.value)

    @get_by.register  # type: ignore[arg-type]
    async def _(self, issue_number: IssueNumber) -> ComicResponseData:
        return await self._get_by(issue_number, ComicModel.number == issue_number.value)

    @get_by.register  # type: ignore[arg-type]
    async def _(self, slug: str) -> ComicResponseData:
        return await self._get_by(slug, ComicModel.slug == slug)

    async def _get_by(
        self,
        value: ComicId | IssueNumber | str,
        where_clause: ColumnElement[bool],
    ) -> ComicResponseData:
        stmt = (
            select(ComicModel)
            .outerjoin(ComicModel.tags)
            .join(ComicModel.translations)
            .outerjoin(TranslationModel.images)
            .options(
                contains_eager(ComicModel.tags),
                contains_eager(ComicModel.translations).options(
                    contains_eager(TranslationModel.images)
                ),
            )
            .where(
                where_clause,
                TranslationModel.status == TranslationStatus.PUBLISHED,
            )
        )

        comic: ComicModel | None = (await self.session.scalars(stmt)).unique().one_or_none()

        if not comic:
            raise ComicNotFoundError(value)

        return map_comic_model_to_data(comic)

    async def get_list(
        self,
        filters: ComicFilters,
        pagination: Pagination,
    ) -> tuple[int, Sequence[ComicCompactResponseData]]:
        first_image_subquery = (
            select(
                ImageModel.image_id,
                ImageModel.original_path,
                ImageModel.converted_path,
                ImageModel.link_id,
                func.row_number()
                .over(
                    partition_by=ImageModel.link_id,
                    order_by=ImageModel.image_id.asc(),
                )
                .label("rn"),
            )
            .where(
                ImageModel.link_type == ImageLinkType.TRANSLATION,
                ImageModel.is_deleted.is_(false()),
            )
            .correlate(TranslationModel)
            .subquery()
        )

        stmt = (
            select(
                ComicModel.comic_id,
                ComicModel.number,
                ComicModel.publication_date,
                TranslationModel.title,
                first_image_subquery.c.original_path,
                first_image_subquery.c.converted_path,
            )
            .join(ComicModel.translations)
            .outerjoin(
                target=first_image_subquery,
                onclause=and_(
                    first_image_subquery.c.link_id == TranslationModel.translation_id,
                    first_image_subquery.c.rn == 1,
                ),
            )
            .limit(pagination.limit)
            .offset(pagination.offset)
            .where(
                TranslationModel.language == filters.search_language,
                TranslationModel.status == TranslationStatus.PUBLISHED,
            )
        )

        if filters.search_query:
            search_subquery = (
                select(TranslationModel.comic_id)
                .where(
                    TranslationModel.comic_id == ComicModel.comic_id,
                    TranslationModel.searchable_text.op("&@")(filters.search_query),
                )
                .correlate(ComicModel)
                .correlate(TranslationModel)
            )

            stmt = stmt.where(exists(search_subquery))

        if filters.date_range.start:
            stmt = stmt.where(ComicModel.publication_date >= filters.date_range.start)
        if filters.date_range.end:
            stmt = stmt.where(ComicModel.publication_date <= filters.date_range.end)

        if filters.tag_slugs:
            tag_subquery = (
                select(ComicTagAssociation.comic_id)
                .join(TagModel)
                .where(TagModel.slug.in_(filters.tag_slugs))
                .group_by(ComicTagAssociation.comic_id)
            )

            if filters.tag_combination == TagCombination.AND and len(filters.tag_slugs) > 1:
                tag_subquery = tag_subquery.having(
                    and_(func.count(TagModel.tag_id) == len(filters.tag_slugs))
                )

            stmt = stmt.where(
                exists(tag_subquery.where(ComicModel.comic_id == ComicTagAssociation.comic_id))
            )

        if pagination.order == SortOrder.ASC:
            stmt = stmt.order_by(ComicModel.number.asc())
        else:
            stmt = stmt.order_by(ComicModel.number.desc())

        rows: Result[ComicCompactRow] = await self.session.execute(stmt)

        count, results = 0, []
        for row in rows:
            results.append(map_row_to_compact_data(row))
            count += 1

        return count, results

    async def get_issue_number_by_id(self, comic_id: ComicId) -> IssueNumber | None:
        stmt = select(ComicModel.number).where(ComicModel.comic_id == comic_id.value)

        number: int | None = await self.session.scalar(stmt)

        return IssueNumber(number) if number else None

    async def get_latest_issue_number(self) -> IssueNumber | None:
        number: int | None = await self.session.scalar(
            select(ComicModel.number).limit(1).order_by(ComicModel.number.desc())
        )

        return IssueNumber(number) if number else None

    async def get_translations(
        self,
        comic_id: ComicId,
        language: Language | None = None,
        status: TranslationStatus | None = None,
    ) -> list[TranslationResponseData]:
        stmt = (
            select(TranslationModel)
            .outerjoin(TranslationModel.images)
            .options(contains_eager(TranslationModel.images))
            .where(TranslationModel.comic_id == comic_id.value)
        )

        if language:
            stmt = stmt.where(TranslationModel.language == language)
        if status:
            stmt = stmt.where(TranslationModel.status == status)

        translations: Sequence[TranslationModel] = (await self.session.scalars(stmt)).unique().all()

        return [map_translation_model_to_data(translation) for translation in translations]

    async def relink_tags(self, comic_id: ComicId, tag_ids: Sequence[TagId]) -> None:
        await self.session.execute(
            delete(ComicTagAssociation).where(ComicTagAssociation.comic_id == comic_id.value)
        )

        if tag_ids:
            try:
                await self.session.execute(
                    insert(ComicTagAssociation).values(
                        [
                            {
                                "comic_id": comic_id.value,
                                "tag_id": tag_id.value,
                            }
                            for tag_id in tag_ids
                        ]
                    )
                )
            except IntegrityError as err:
                self._handle_db_error(err)

    async def load(self, comic_id: ComicId) -> ComicEntity:  # TODO: with_for_update?
        stmt = (
            select(ComicModel)
            .join(TranslationModel)
            .where(
                ComicModel.comic_id == comic_id.value,
                TranslationModel.language == Language.EN,
            )
            .options(contains_eager(ComicModel.translations))
        )

        comic: ComicModel | None = (await self.session.scalars(stmt)).unique().one_or_none()

        if comic is None:
            raise ComicNotFoundError(comic_id)

        return map_comic_model_to_entity(comic)

    def _handle_db_error(
        self,
        err: DBAPIError,
        *,
        entity: ComicEntity | None = None,
    ) -> NoReturn:
        cause = str(err.__cause__)

        if "fk_comic_tag_association_tag_id_tags" in cause:
            if match := re.search(TAG_ID_PATTERN, cause):
                raise TagNotFoundError(tag_id=int(match.group(1)))
        elif entity and entity.number and "uq_comic_number_if_not_extra" in cause:
            raise ComicNumberAlreadyExistsError(entity.number)
        elif entity and "uq_comic_title_if_extra" in cause:
            raise ExtraComicTitleAlreadyExistsError(entity.title)

        raise RepoError from err
