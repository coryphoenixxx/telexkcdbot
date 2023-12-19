from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.comics.dtos import ComicCreateDTO
from src.app.comics.models import ComicModel, ComicTagAssociation, TagModel


class ComicRepo:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, comic_dto: ComicCreateDTO) -> ComicModel:
        tags = await self.add_tags(comic_dto.tags)

        stmt = insert(ComicModel).values(comic_dto.to_dict(exclude=("tags", "translation"))).returning(ComicModel)

        comic = await self._session.scalar(stmt)

        stmt = insert(ComicTagAssociation).values([{"comic_id": comic.issue_number, "tag_id": tag.id} for tag in tags])
        await self._session.execute(stmt)

        return comic

    async def add_tags(self, tags: list[str]) -> Sequence[TagModel]:
        stmt = insert(TagModel).values([{"name": tag_name} for tag_name in tags])
        update_stmt = stmt.on_conflict_do_update(
            constraint="uq_tags_name", set_={"name": stmt.excluded.name},
        ).returning(TagModel)

        result = (await self._session.scalars(update_stmt)).all()

        return result

    async def get_extra_num(self) -> int:
        stmt = select(func.count("*")).select_from(ComicModel).where(ComicModel.is_extra is True)
        extra_num = await self._session.scalar(stmt)
        return extra_num
