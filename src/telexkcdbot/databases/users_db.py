import json
from asyncpg import Pool

from datetime import date, timedelta


class UsersDatabase:
    pool: Pool

    async def create(self, pool: Pool):
        self.pool = pool

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

    async def get_last_week_active_users_num(self) -> int:
        query = """SELECT array_agg(last_action_date) FROM users;"""

        res = await self.pool.fetchval(query)

        return sum(((date.today() - d) < timedelta(days=7) for d in res))

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

        return tuple(res) if res else ()  # TODO: namedtuple

    async def toggle_subscription_status(self, user_id: int):
        get_query = """SELECT is_subscribed FROM users
                       WHERE user_id = $1;"""

        set_query = """UPDATE users SET is_subscribed = $1
                       WHERE user_id = $2;"""

        async with self.pool.acquire() as conn:
            cur_value = await conn.fetchval(get_query, user_id)
            await conn.execute(set_query, not cur_value, user_id)


users_db = UsersDatabase()
