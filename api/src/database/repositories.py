from pathlib import Path

import aiofiles
from aiofiles import os
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src import dtos
from src.database import models


class ComicsRepo:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, comic_dto: dtos.ComicRequestDto) -> models.Comic:
        async with self._session, self._session.begin():
            translations = []
            for lang_code, content in comic_dto.translations.items():
                translations.append(
                    models.ComicTranslation(
                        comic_id=comic_dto.comic_id,
                        language_code=lang_code,
                        **content.to_dict(),
                    ),
                )

            comic_model = models.Comic(
                **comic_dto.to_dict(exclude=('translations',)),
                translations=translations,
            )

            self._session.add(comic_model)

            comic_model = (await self._session.scalars(self._get_by_id_stmt(comic_model.comic_id))).one()

            await self._session.commit()

        return comic_model

    async def get_by_id(self, comic_id: int) -> models.Comic | None:
        async with self._session:
            comic_model: models.Comic = (await self._session.scalars(self._get_by_id_stmt(comic_id))).one_or_none()
            return comic_model

    # async def get_list(
    #         self,
    #         limit: int | None,
    #         offset: int | None,
    #         order: types.OrderType,
    # ) -> tuple[list[types.ComicDTO], int]:
    #     async with self._session_factory() as session, session.begin():
    #         stmt = select(models.Comic) \
    #             .options(selectinload(models.Comic.translations)) \
    #             .limit(limit) \
    #             .offset(offset)
    #         if order == 'desc':
    #             stmt = stmt.order_by(models.Comic.comic_id.desc())
    #
    #         result = (await session.scalars(stmt)).unique().all()
    #
    #         total = await session.scalar(models.Comic.total_count)
    #
    #         return [comic.to_dto() for comic in result], total
    #
    # async def search(
    #         self,
    #         q: str,
    #         limit: int | None,
    #         offset: int | None,
    # ) -> tuple[list[types.ComicDTO], int]:
    #     async with self._session_factory() as session, session.begin():
    #         stmt = select(models.Comic) \
    #             .join(models.Comic.translations) \
    #             .options(selectinload(models.Comic.translations)) \
    #             .where(models.ComicTranslation.search_vector.match(q)) \
    #             .limit(limit) \
    #             .offset(offset)
    #
    #         comics = (await session.scalars(stmt)).unique().all()
    #         total = await session.scalar(models.Comic.total_count)
    #
    #         return [comic.to_dto() for comic in comics], total
    #

    #
    # async def update(self, comic_id: int, new_comic_data: types.PutComic) -> types.ComicDTO | None:
    #     async with self._session_factory() as session, session.begin():
    #         translations = [{'comic_id': comic_id} | tr.model_dump() for tr in new_comic_data.translations]
    #
    #         await session.execute(update(models.ComicTranslation), translations)
    #
    #         stmt = update(models.Comic).values(
    #             comic_id=comic_id,
    #             **new_comic_data.model_dump(exclude={'translations'}),
    #         )
    #
    #         await session.execute(stmt)
    #
    #         comic = (await session.scalars(self._get_by_id_stmt(comic_id))).one()
    #
    #         return comic.to_dto()
    #
    # async def delete(self, comic_id: int) -> int:
    #     async with self._session_factory() as session, session.begin():
    #         stmt = delete(models.Comic) \
    #             .where(models.Comic.comic_id == comic_id) \
    #             .returning(models.Comic.comic_id)
    #
    #         comic_id = await session.scalar(stmt)
    #
    #         return comic_id

    @staticmethod
    def _get_by_id_stmt(comic_id: int):
        return select(models.Comic) \
            .options(selectinload(models.Comic.translations)) \
            .where(models.Comic.comic_id == comic_id)


class ComicFilesRepo:
    root = '../static/images'

    async def save(self, dst_path: str | Path, file: bytearray) -> str:
        full_path = Path(self.root + dst_path)
        await os.makedirs(full_path.parent, exist_ok=True)
        async with aiofiles.open(full_path, 'wb') as f:
            await f.write(file)
        return str(full_path)

    async def get(self, path):
        ...

    async def delete(self, path):
        ...
