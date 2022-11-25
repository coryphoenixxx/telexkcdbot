from dataclasses import astuple

import asyncpg

from api.models import TotalComicData


class Comics:
    pool: asyncpg.Pool

    async def add_new_comic(self, comic_data: TotalComicData) -> None:
        query = """INSERT INTO comics (comic_id,
                                       title,
                                       img_url,
                                       comment,
                                       public_date,
                                       is_specific,
                                       ru_title,
                                       ru_img_url,
                                       ru_comment,
                                       has_ru_translation)
                   VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9,$10)
                   ON CONFLICT (comic_id) DO NOTHING;"""

        await self.pool.execute(query, *astuple(comic_data))

    async def toggle_spec_status(self, comic_id: int) -> None:
        query = """UPDATE comics
                   SET is_specific = NOT is_specific
                   WHERE comic_id = $1;"""

        await self.pool.execute(query, comic_id)
