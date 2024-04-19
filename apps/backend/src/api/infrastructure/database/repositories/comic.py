from shared.types import Order
from sqlalchemy import delete, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import noload
from sqlalchemy.sql.selectable import ForUpdateArg, ForUpdateParameter

from api.application.dtos.requests.comic import ComicRequestDTO
from api.application.dtos.responses import TranslationResponseDTO
from api.application.dtos.responses.comic import ComicResponseDTO, ComicResponseWTranslationsDTO
from api.application.exceptions.comic import (
    ComicByIDNotFoundError,
    ComicByIssueNumberNotFoundError,
    ComicBySlugNotFoundError,
    ComicNumberAlreadyExistsError,
    ExtraComicTitleAlreadyExistsError,
)
from api.infrastructure.database.models import TranslationModel
from api.infrastructure.database.models.comic import ComicModel, TagModel
from api.infrastructure.database.repositories.base import BaseRepo
from api.infrastructure.database.repositories.mixins import GetImagesMixin
from api.infrastructure.database.types import ComicFilterParams, TagParam
from api.infrastructure.database.utils import build_searchable_text
from api.types import ComicID, IssueNumber, Language, TotalCount
from api.utils import slugify


class ComicRepo(BaseRepo, GetImagesMixin):
    async def create(
        self,
        dto: ComicRequestDTO,
    ) -> ComicResponseDTO:
        images = await self._get_images_by_ids(dto.image_ids)
        tags = await self._create_tags(dto.tags)

        comic = ComicModel(
            number=dto.number,
            slug=self._build_slug(dto.number, dto.title),
            publication_date=dto.publication_date,
            explain_url=dto.explain_url,
            click_url=dto.click_url,
            is_interactive=dto.is_interactive,
            tags=tags,
            translations=[
                TranslationModel(
                    title=dto.title,
                    language=Language.EN,
                    tooltip=dto.tooltip,
                    raw_transcript=dto.raw_transcript,
                    translator_comment="",
                    source_url=dto.xkcd_url,
                    images=images,
                    is_draft=False,
                    searchable_text=build_searchable_text(dto.title, dto.raw_transcript),
                ),
            ],
        )

        self._session.add(comic)

        try:
            await self._session.flush()
        except IntegrityError as err:
            self._handle_db_error(err, dto)
        else:
            await self._session.refresh(comic)
            return ComicResponseDTO.from_model(comic)

    async def update(
        self,
        comic_id: ComicID,
        dto: ComicRequestDTO,
    ) -> ComicResponseDTO:
        comic: ComicModel = await self._get_by_id(
            comic_id,
            with_for_update=ForUpdateArg(of=ComicModel),
        )

        images = await self._get_images_by_ids(dto.image_ids)
        tags = await self._create_tags(dto.tags)

        comic.number = dto.number
        comic.slug = self._build_slug(dto.number, dto.title)
        comic.publication_date = dto.publication_date
        comic.explain_url = dto.explain_url
        comic.click_url = dto.click_url
        comic.is_interactive = dto.is_interactive
        comic.tags = tags

        comic.original.title = dto.title
        comic.original.tooltip = dto.tooltip
        comic.original.raw_transcript = dto.raw_transcript
        comic.original.images = images
        comic.original.xkcd_url = dto.xkcd_url

        try:
            await self._session.flush()
        except IntegrityError as err:
            self._handle_db_error(err, dto)
        else:
            return ComicResponseDTO.from_model(comic)

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

        return ComicResponseWTranslationsDTO.from_model(comic)

    async def get_by_issue_number(self, number: IssueNumber) -> ComicResponseWTranslationsDTO:
        stmt = select(ComicModel).where(ComicModel.number == number)

        comic: ComicModel | None = (await self._session.scalars(stmt)).unique().one_or_none()

        if not comic:
            raise ComicByIssueNumberNotFoundError(number=number)

        return ComicResponseWTranslationsDTO.from_model(comic)

    async def get_by_slug(self, slug: str) -> ComicResponseWTranslationsDTO:
        stmt = select(ComicModel).where(ComicModel.slug == slug)

        comic: ComicModel | None = (await self._session.scalars(stmt)).unique().one_or_none()

        if not comic:
            raise ComicBySlugNotFoundError(slug=slug)

        return ComicResponseWTranslationsDTO.from_model(comic)

    async def get_list(
        self,
        filter_params: ComicFilterParams,
    ) -> tuple[TotalCount, list[ComicResponseWTranslationsDTO]]:
        stmt = select(ComicModel, func.count(ComicModel.comic_id).over().label("total"))

        if filter_params.q:
            subq = select(TranslationModel.comic_id).where(
                TranslationModel.searchable_text.op("&@")(filter_params.q),
            )
            stmt = stmt.where(ComicModel.comic_id.in_(subq))

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

        stmt = stmt.limit(filter_params.limit).offset(filter_params.offset)

        print((await self._session.scalars(stmt)).unique().all())

        total, comics = 0, []
        if result := (await self._session.execute(stmt)).unique().all():
            total, comics = result[0][1], [r[0] for r in result]

        return total, [ComicResponseWTranslationsDTO.from_model(comic) for comic in comics]

    async def get_translations(
        self,
        comic_id: ComicID,
        is_draft: bool = False,
    ) -> list[TranslationResponseDTO]:
        comic = await self._get_by_id(comic_id)

        if is_draft:
            return [TranslationResponseDTO.from_model(model) for model in comic.translation_drafts]
        return [TranslationResponseDTO.from_model(model) for model in comic.translations]

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
        with_for_update: ForUpdateParameter = False,
    ) -> ComicModel:
        comic = await self._session.get(ComicModel, comic_id, with_for_update=with_for_update)

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
