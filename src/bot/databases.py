import asyncpg
import json

from datetime import date, timedelta

from .config import HEROKU


async def create_pool(db_url) -> asyncpg.Pool:
    if HEROKU:
        db_url += '?sslmode=require'
    return await asyncpg.create_pool(db_url, max_size=20)


class UsersDatabase:
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool

    async def create(self):
        query = """CREATE TABLE IF NOT EXISTS users (
                     id SERIAL NOT NULL,
                     user_id INTEGER UNIQUE,
                     cur_comic_info VARCHAR(10) DEFAULT '0_en', 
                     bookmarks JSON DEFAULT '[]',
                     is_subscribed INTEGER DEFAULT 1, 
                     user_lang VARCHAR(2) DEFAULT 'ru',
                     last_action_date DATE DEFAULT CURRENT_DATE);                    

                   CREATE UNIQUE INDEX IF NOT EXISTS user_id_uindex ON users (id);"""

        await self.pool.execute(query)

    """USER"""

    async def add_user(self, user_id: int):
        query = """INSERT INTO users (user_id)
                   VALUES($1)
                   ON CONFLICT (user_id) DO NOTHING;"""

        await self.pool.execute(query, user_id)

    async def delete_user(self, user_id: int):
        query = """DELETE FROM users
                   WHERE user_id = $1;"""

        await self.pool.execute(query, user_id)

    async def get_cur_comic_info(self, user_id: int) -> (int, str):
        query = """SELECT cur_comic_info FROM users 
                   WHERE user_id = $1;"""

        res = await self.pool.fetchval(query, user_id)
        comic_id, comic_lang = res.split('_')

        return int(comic_id), comic_lang

    async def get_all_users_ids(self) -> tuple:
        query = """SELECT array_agg(user_id) FROM users;"""

        res = await self.pool.fetchval(query)

        return tuple(res) if res else ()

    async def get_user_lang(self, user_id):
        """For handling LANG button"""
        query = """SELECT user_lang FROM users
                   WHERE user_id = $1;"""

        res = await self.pool.fetchval(query, user_id)

        return res

    async def set_user_lang(self, user_id: int, user_lang: str):
        """For handling LANG button"""
        query = """UPDATE users SET user_lang = $1
                   WHERE user_id = $2;"""

        await self.pool.execute(query, user_lang, user_id)

    async def update_cur_comic_info(self, user_id: int, new_cur_comic_id: int, new_cur_comic_lang: str):
        query = """UPDATE users SET cur_comic_info = $1
                   WHERE user_id = $2;"""

        cur_comic_info = str(new_cur_comic_id) + '_' + new_cur_comic_lang
        await self.pool.execute(query, cur_comic_info, user_id)

    async def update_last_action_date(self, user_id: int, action_date: date):
        query = """UPDATE users SET last_action_date = $1
                   WHERE user_id = $2;"""

        await self.pool.execute(query, action_date, user_id)

    async def get_last_month_active_users_num(self) -> int:
        query = """SELECT array_agg(last_action_date) FROM users;"""

        res = await self.pool.fetchval(query)

        return sum(((date.today() - d) < timedelta(days=30) for d in res))

    """BOOKMARKS"""

    async def get_bookmarks(self, user_id: int) -> list:
        query = """SELECT bookmarks FROM users
                   WHERE user_id = $1;"""

        res = await self.pool.fetchval(query, user_id)

        return json.loads(res)

    async def update_bookmarks(self, user_id: int, new_bookmarks: list):
        query = """UPDATE users SET bookmarks = $1
                   WHERE user_id = $2;"""

        new_bookmarks_json = json.dumps(new_bookmarks)
        await self.pool.execute(query, new_bookmarks_json, user_id)

    """SUBSCRIPTION"""

    async def get_subscribed_users(self) -> tuple:
        query = """SELECT array_agg(user_id) FROM users
                   WHERE is_subscribed = 1;"""

        res = await self.pool.fetchval(query)

        return tuple(res) if res else ()

    async def toggle_subscription_status(self, user_id: int):
        get_query = """SELECT is_subscribed FROM users
                       WHERE user_id = $1;"""

        set_query = """UPDATE users SET is_subscribed = $1
                       WHERE user_id = $2;"""

        async with self.pool.acquire() as conn:
            cur_value = await conn.fetchval(get_query, user_id)
            await conn.execute(set_query, not cur_value, user_id)


class ComicsDatabase:
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool

    async def create(self):
        query = """CREATE TABLE IF NOT EXISTS comics (
                     id SERIAL NOT NULL,
                     comic_id INTEGER NOT NULL UNIQUE,
                     title VARCHAR(128) DEFAULT '...',
                     img_url VARCHAR(512) DEFAULT '',
                     comment TEXT DEFAULT '...',
                     public_date DATE NOT NULL DEFAULT CURRENT_DATE,
                     is_specific INTEGER NOT NULL DEFAULT 0,
                     ru_title VARCHAR(128) DEFAULT '...',
                     ru_img_url VARCHAR(512) DEFAULT '...',
                     ru_comment TEXT DEFAULT '...');
    
                   CREATE UNIQUE INDEX IF NOT EXISTS comic_id_uindex ON comics (comic_id);"""

        await self.pool.execute(query)

    async def add_new_comic(self, comic_values: tuple):
        query = """INSERT INTO comics (comic_id,
                                       title,
                                       img_url,
                                       comment,
                                       public_date,
                                       is_specific,
                                       ru_title,
                                       ru_img_url,
                                       ru_comment)
                   VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9)
                   ON CONFLICT (comic_id) DO NOTHING;"""

        await self.pool.execute(query, *comic_values)

    async def get_all_comics_ids(self) -> tuple:
        query = """SELECT array_agg(comic_id) FROM comics;"""

        res = await self.pool.fetchval(query)

        return tuple(res) if res else ()

    async def get_last_comic_id(self) -> int:
        query = """SELECT comic_id FROM comics
                   ORDER BY comic_id DESC;"""

        res = await self.pool.fetchval(query)

        return res

    async def get_comic_data_by_id(self, comic_id: int) -> tuple:
        query = """SELECT comic_id, title, img_url, comment, public_date, is_specific FROM comics
                   WHERE comic_id = $1;"""

        res = await self.pool.fetchrow(query, comic_id)

        return tuple(res)

    async def get_ru_comic_data_by_id(self, comic_id: int) -> tuple:
        query = """SELECT comic_id, ru_title, ru_img_url, ru_comment, public_date, is_specific FROM comics
                   WHERE comic_id = $1;"""

        res = await self.pool.fetchrow(query, comic_id)

        return tuple(res)

    async def get_comics_info_by_title(self, title: str) -> list:
        query = """SELECT array_agg(comic_id), array_agg(title), array_agg(ru_title) FROM comics
                    
                     WHERE title = $1
                     OR title ILIKE format('%s %s%s', '%', $1, '%')
                     OR title ILIKE format('%s%s', $1, '%')
                     OR title ILIKE format('%s%s %s', '%', $1, '%')
                     OR title ILIKE format('%s%s', '%', $1)
                     OR title ILIKE format('%s%s, %s', '%', $1, '%')
                     OR title ILIKE format('%s%s-%s', '%', $1, '%')
                     OR title ILIKE format('%s-%s%s', '%', $1, '%')

                     OR ru_title = $1
                     OR ru_title ILIKE format('%s %s%s', '%', $1, '%')
                     OR ru_title ILIKE format('%s%s', $1, '%')
                     OR ru_title ILIKE format('%s%s %s', '%', $1, '%')
                     OR ru_title ILIKE format('%s%s', '%', $1)
                     OR ru_title ILIKE format('%s%s, %s', '%', $1, '%')
                     OR ru_title ILIKE format('%s%s-%s', '%', $1, '%')
                     OR ru_title ILIKE format('%s-%s%s', '%', $1, '%');"""

        res = await self.pool.fetchrow(query, title)

        if not res[0]:
            return []
        else:
            z = zip(res[0], res[1], res[2])
            info = [(_id, title, ru_title) for _id, title, ru_title in sorted(z, key=lambda x: len(x[1]))]
            return list(zip(*info))

    async def toggle_spec_status(self, comic_id: int):
        get_query = """SELECT is_specific FROM comics
                       WHERE comic_id = $1;"""

        set_query = """UPDATE comics SET is_specific = $1
                       WHERE comic_id = $2;"""

        async with self.pool.acquire() as conn:
            cur_value = await conn.fetchval(get_query, comic_id)
            await conn.execute(set_query, not cur_value, comic_id)


if __name__ == "__main__":
    # Needs envs
    import asyncio
    from src.bot.fill_comics_db import fill_comics_db

    loop = asyncio.get_event_loop()
    loop.run_until_complete(fill_comics_db())
