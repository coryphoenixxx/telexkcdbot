from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import joinedload

from api.application.dtos.common import TagName
from api.core.value_objects import ComicID
from api.infrastructure.database.models import ComicModel, TagModel
from api.infrastructure.database.repositories.base import BaseRepo


class TagRepo(BaseRepo):
    async def create_many(self, comic_id: ComicID, names: Sequence[TagName]) -> None:
        if not names:
            return

        await self._session.execute(
            insert(TagModel)
            .values([{"name": name} for name in names])
            .on_conflict_do_nothing(constraint="uq_tags_name")
        )

        tags = (await self._session.scalars(select(TagModel).where(TagModel.name.in_(names)))).all()

        comic = await self._get_model_by_id(
            ComicModel, comic_id, options=(joinedload(ComicModel.tags),)
        )
        comic.tags = tags

    async def delete(self, name: TagName) -> None: ...
