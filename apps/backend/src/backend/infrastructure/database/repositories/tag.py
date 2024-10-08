from collections.abc import Iterable, Sequence
from typing import NoReturn

from sqlalchemy import delete, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import DBAPIError, IntegrityError

from backend.application.comic.exceptions import TagNameAlreadyExistsError, TagNotFoundError
from backend.application.comic.interfaces import TagRepoInterface
from backend.application.comic.responses import TagResponseData
from backend.domain.entities import NewTagEntity, TagEntity
from backend.domain.value_objects import TagId, TagName
from backend.infrastructure.database.mappers import map_tag_model_to_data, map_tag_model_to_entity
from backend.infrastructure.database.models import TagModel
from backend.infrastructure.database.repositories import BaseRepo, RepoError


class TagRepo(BaseRepo, TagRepoInterface):
    async def create(self, tag: NewTagEntity) -> TagId:
        stmt = (
            insert(TagModel)
            .values(
                name=tag.name.value,
                slug=tag.slug,
                is_visible=tag.is_visible,
                from_explainxkcd=tag.from_explainxkcd,
            )
            .returning(TagModel.tag_id)
        )

        try:
            tag_id: int = await self.session.scalar(stmt)  # type: ignore[assignment]
        except IntegrityError as err:
            self._handle_db_error(err, tag_name=tag.name)

        return TagId(tag_id)

    async def create_many(self, tags: Sequence[NewTagEntity]) -> Sequence[TagId]:
        if not tags:
            return []

        stmt = select(TagModel).where(TagModel.slug.in_(t.slug for t in tags))

        existing_db_tags: Iterable[TagModel] = (await self.session.scalars(stmt)).all()

        db_tag_slugs = {t.slug for t in existing_db_tags}
        new_tags = [t for t in tags if t.slug not in db_tag_slugs]

        if new_tags:
            await self.session.execute(
                insert(TagModel)
                .values(
                    [
                        {
                            "name": tag.name.value,
                            "slug": tag.name.slug,
                            "is_visible": tag.is_visible,
                            "from_explainxkcd": tag.from_explainxkcd,
                        }
                        for tag in new_tags
                    ]
                )
                .on_conflict_do_nothing(constraint="uq_tags_slug")
            )

            new_db_tags: Iterable[TagModel] = (await self.session.scalars(stmt)).all()

            return [TagId(tag.tag_id) for tag in new_db_tags]

        return [TagId(tag.tag_id) for tag in existing_db_tags]

    async def update(self, tag: TagEntity) -> None:
        stmt = (
            update(TagModel)
            .values(
                name=tag.name.value,
                slug=tag.slug,
                is_visible=tag.is_visible,
                from_explainxkcd=tag.from_explainxkcd,
            )
            .where(TagModel.tag_id == tag.id.value)
        )

        try:
            await self.session.execute(stmt)
        except IntegrityError as err:
            self._handle_db_error(err, tag_name=tag.name)

    async def delete(self, tag_id: TagId) -> None:
        await self.session.execute(delete(TagModel).where(TagModel.tag_id == tag_id.value))

    async def get_by_id(self, tag_id: TagId) -> TagResponseData:
        return map_tag_model_to_data(tag=await self._get_by_id(tag_id))

    async def load(self, tag_id: TagId) -> TagEntity:
        return map_tag_model_to_entity(tag=await self._get_by_id(tag_id))  # TODO: with_for_update?

    async def _get_by_id(self, tag_id: TagId) -> TagModel:
        tag = await self.session.get(TagModel, tag_id.value)
        if tag is None:
            raise TagNotFoundError(tag_id.value)
        return tag

    def _handle_db_error(self, err: DBAPIError, *, tag_name: TagName) -> NoReturn:
        cause = str(err.__cause__)

        if "uq_tags_slug" in cause:
            raise TagNameAlreadyExistsError(tag_name.value)

        raise RepoError from err  # TODO: check
