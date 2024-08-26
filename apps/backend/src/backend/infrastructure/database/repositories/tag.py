from collections.abc import Sequence
from dataclasses import dataclass
from typing import NoReturn

from sqlalchemy import delete, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.orm import joinedload

from backend.application.dtos import TagResponseDTO
from backend.application.dtos.requests import TagUpdateDTO
from backend.core.exceptions.base import BaseAppError
from backend.core.value_objects import ComicID, TagID, TagName
from backend.infrastructure.database.models import ComicModel, TagModel
from backend.infrastructure.database.repositories.base import BaseRepo, RepoError
from backend.infrastructure.utils import slugify


@dataclass(slots=True, eq=False)
class TagNotFoundError(BaseAppError):
    tag_id: int

    @property
    def message(self) -> str:
        return f"A tag (id={self.tag_id}) not found."


@dataclass(slots=True, eq=False)
class TagNameUniqueError(BaseAppError):
    name: str

    @property
    def message(self) -> str:
        return f"A tag name ({self.name}) already exists."


@dataclass(slots=True, eq=False)
class TempTag:
    name: str
    slug: str | None = None

    def __post_init__(self) -> None:
        self.slug = slugify(self.name)


class TagRepo(BaseRepo):
    async def create_many(
        self,
        comic_id: ComicID,
        tag_names: Sequence[TagName],
    ) -> Sequence[TagResponseDTO]:
        if not tag_names:
            return []

        temp_tag_objs = [TempTag(name) for name in sorted(set(tag_names))]

        stmt = select(TagModel).where(TagModel.slug.in_(t.slug for t in temp_tag_objs))

        db_tags = (await self._session.scalars(stmt)).all()

        db_tag_slugs = {tag.slug for tag in db_tags}
        new_tag_objs = [t for t in temp_tag_objs if t.slug not in db_tag_slugs]

        if new_tag_objs:
            await self._session.execute(
                insert(TagModel)
                .values([{"name": t.name, "slug": t.slug} for t in new_tag_objs])
                .on_conflict_do_nothing(constraint="uq_tags_slug")
            )

            db_tags = (await self._session.scalars(stmt)).all()

        comic = await self._get_model_by_id(
            ComicModel, comic_id, options=(joinedload(ComicModel.tags),)
        )
        comic.tags = db_tags

        return [TagResponseDTO.from_model(tag) for tag in db_tags]

    async def update(self, tag_id: TagID, dto: TagUpdateDTO) -> TagResponseDTO:
        if dto:
            update_data = dict(dto)
            if name := update_data.get("name"):
                update_data["slug"] = slugify(name)

            stmt = update(TagModel).values(**update_data).where(TagModel.tag_id == tag_id)

            try:
                await self._session.execute(stmt)
            except IntegrityError as err:
                self._handle_db_error(name, err)

        return TagResponseDTO.from_model(await self._get_by_id(tag_id))

    async def delete(self, tag_id: TagID) -> None:
        await self._session.execute(delete(TagModel).where(TagModel.tag_id == tag_id))

    async def _get_by_id(self, tag_id: TagID) -> TagModel:
        tag = await self._get_model_by_id(TagModel, tag_id)
        if not tag:
            raise TagNotFoundError(tag_id)
        return tag

    def _handle_db_error(self, name: str, err: DBAPIError) -> NoReturn:
        cause = str(err.__cause__)

        if "uq_tags_slug" in cause:
            raise TagNameUniqueError(name)

        raise RepoError from err