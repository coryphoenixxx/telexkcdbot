from dataclasses import astuple
from typing import Sequence

import asyncpg

from telexkcdbot.models import ComicData, ComicHeadlineInfo, TotalComicData


class ComicsDatabase:
    pool: asyncpg.Pool

    async def create(self, pool: asyncpg.Pool):
        self.pool = pool
        query = """CREATE TABLE IF NOT EXISTS comics (
                     id SERIAL NOT NULL,
                     comic_id INTEGER NOT NULL UNIQUE,
                     title VARCHAR(128) DEFAULT '...',
                     img_url VARCHAR(512) DEFAULT '',
                     comment TEXT DEFAULT '...',
                     public_date DATE NOT NULL DEFAULT CURRENT_DATE,
                     is_specific BOOLEAN DEFAULT FALSE,
                     ru_title VARCHAR(128) DEFAULT '...',
                     ru_img_url VARCHAR(512) DEFAULT '...',
                     ru_comment TEXT DEFAULT '...',
                     has_ru_translation BOOLEAN DEFAULT FALSE);

                   CREATE UNIQUE INDEX IF NOT EXISTS comic_id_uindex ON comics (comic_id);"""

        await self.pool.execute(query)

    @staticmethod
    async def records_to_headlines_info(records: list[asyncpg.Record],
                                        title_col: str,
                                        img_url_col: str) -> list[ComicHeadlineInfo]:
        headlines_info = []
        for record in records:
            headline_info = ComicHeadlineInfo(comic_id=record['comic_id'],
                                              title=record[title_col],
                                              img_url=record[img_url_col])
            headlines_info.append(headline_info)
        return headlines_info

    async def add_new_comic(self, comic_data: TotalComicData):
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

    async def get_last_comic_id(self) -> int:
        query = """SELECT comic_id FROM comics
                   ORDER BY comic_id DESC
                   LIMIT 1;"""

        return await self.pool.fetchval(query)

    async def get_all_comics_ids(self) -> Sequence[int]:
        query = """SELECT array_agg(comic_id) FROM comics;"""

        res = await self.pool.fetchval(query)
        return tuple(res) if res else ()

    async def get_all_ru_comics_ids(self) -> Sequence[int]:
        query = """SELECT array_agg(comic_id) FROM comics
                   WHERE has_ru_translation = TRUE;"""

        return tuple(await self.pool.fetchval(query))

    async def get_comic_data_by_id(self, comic_id: int, comic_lang: str = 'en') -> ComicData:
        title_col, img_url_col, comment_col = ('title', 'img_url', 'comment') if comic_lang == 'en' \
            else ('ru_title', 'ru_img_url', 'ru_comment')

        query = f"""SELECT comic_id, {title_col}, {img_url_col}, {comment_col}, 
                           public_date, is_specific, has_ru_translation 
                    FROM comics
                    WHERE comic_id = $1;"""

        res = await self.pool.fetchrow(query, comic_id)
        return ComicData(*res)

    async def get_comics_headlines_info_by_title(self, title: str, lang: str = 'en') -> list[ComicHeadlineInfo]:
        title_col, img_url_col = ('title', 'img_url') if lang == 'en' else ('ru_title', 'ru_img_url')
        query = f"""SELECT comic_id, {title_col}, {img_url_col} FROM comics

                     WHERE {title_col} = $1
                     OR {title_col} ILIKE format('%s %s%s', '%', $1, '%')
                     OR {title_col} ILIKE format('%s%s', $1, '%')
                     OR {title_col} ILIKE format('%s%s %s', '%', $1, '%')
                     OR {title_col} ILIKE format('%s%s', '%', $1)
                     OR {title_col} ILIKE format('%s%s, %s', '%', $1, '%')
                     OR {title_col} ILIKE format('%s%s-%s', '%', $1, '%')
                     OR {title_col} ILIKE format('%s-%s%s', '%', $1, '%')"""

        res = await self.pool.fetch(query, title)
        if not res:
            return []
        return await self.records_to_headlines_info(sorted(res, key=lambda x: len(x[title_col])),
                                                    title_col,
                                                    img_url_col)

    async def get_comics_headlines_info_by_ids(self, ids: list, lang: str = 'en') -> list[ComicHeadlineInfo]:
        title_col, img_url_col = ('title', 'img_url') if lang == 'en' else ('ru_title', 'ru_img_url')

        query = f"""SELECT comic_id, {title_col}, {img_url_col} FROM comics
                    WHERE comic_id in {tuple(ids)};"""

        res = await self.pool.fetch(query)
        headlines_info = await self.records_to_headlines_info(res, title_col, img_url_col)
        return [h for h in sorted(headlines_info, key=lambda x: ids.index(x.comic_id))]  # Saved order of ids list

    async def toggle_spec_status(self, comic_id: int):
        query = """UPDATE comics 
                   SET is_specific = NOT is_specific 
                   WHERE comic_id = $1;"""

        await self.pool.execute(query, comic_id)


comics_db = ComicsDatabase()
