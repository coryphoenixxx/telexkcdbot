from collections.abc import Sequence
from dataclasses import dataclass
from typing import NoReturn

from sqlalchemy import delete, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.orm import joinedload

from api.application.dtos.common import TagName
from api.application.dtos.responses import TagResponseDTO
from api.core.exceptions.tag import TagNameUniqueError, TagNotFoundError
from api.core.utils import slugify
from api.core.value_objects import ComicID, TagID
from api.infrastructure.database.models import ComicModel, TagModel
from api.infrastructure.database.repositories.base import BaseRepo


@dataclass(slots=True)
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

    async def delete(self, tag_id: TagID) -> None:
        await self._session.execute(delete(TagModel).where(TagModel.tag_id == tag_id))

    async def update(self, tag_id: TagID, name: str, blacklist_status: bool) -> TagResponseDTO:
        stmt = (
            update(TagModel)
            .values(
                name=name,
                slug=slugify(name),
                is_blacklisted=blacklist_status,
            )
            .where(TagModel.tag_id == tag_id)
            .returning(TagModel)
        )

        try:
            tag = (await self._session.scalars(stmt)).one_or_none()
        except IntegrityError as err:
            self._handle_db_error(err)

        if not tag:
            raise TagNotFoundError

        return TagResponseDTO.from_model(tag)

    def _handle_db_error(self, err: DBAPIError) -> NoReturn:
        cause = str(err.__cause__)

        if "uq_tags_slug" in cause:
            raise TagNameUniqueError

        raise err
