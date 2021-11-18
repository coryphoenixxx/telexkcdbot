import json
import asyncpg

from datetime import date, timedelta


class UsersDatabase:
    pool: asyncpg.Pool

    async def create(self, pool: asyncpg.Pool):
        self.pool = pool

        query = """CREATE TABLE IF NOT EXISTS users (
                     id SERIAL NOT NULL,
                     user_id INTEGER UNIQUE,
                     user_lang VARCHAR(2) DEFAULT 'en',
                     cur_comic_info VARCHAR(10) DEFAULT '0_en', 
                     bookmarks JSON DEFAULT '[]',
                     is_subscribed BOOLEAN DEFAULT TRUE,
                     notification_sound_status BOOLEAN DEFAULT FALSE,
                     lang_btn_status BOOLEAN DEFAULT TRUE,
                     is_banned BOOLEAN DEFAULT FALSE,
                     only_ru_mode BOOLEAN DEFAULT FALSE,
                     last_action_date DATE DEFAULT CURRENT_DATE);                   

                   CREATE UNIQUE INDEX IF NOT EXISTS user_id_uindex ON users (id);"""

        await self.pool.execute(query)

    async def add_user(self, user_id: int):
        query = """INSERT INTO users (user_id)
                   VALUES($1)
                   ON CONFLICT (user_id) DO NOTHING;"""

        await self.pool.execute(query, user_id)

    async def delete_user(self, user_id: int):
        query = """DELETE FROM users
                   WHERE user_id = $1;"""

        await self.pool.execute(query, user_id)

    async def get_cur_comic_info(self, user_id: int) -> tuple[int, str]:
        query = """SELECT cur_comic_info FROM users 
                   WHERE user_id = $1;"""

        res = await self.pool.fetchval(query, user_id)
        comic_id, comic_lang = res.split('_')
        return int(comic_id), comic_lang

    async def get_all_users_ids(self) -> tuple[int]:
        query = """SELECT array_agg(user_id) FROM users;"""

        res = await self.pool.fetchval(query)
        return tuple(res) if res else ()

    async def get_only_ru_mode_status(self, user_id: int) -> bool:
        query = """SELECT only_ru_mode FROM users 
                   WHERE user_id = $1;"""

        res = await self.pool.fetchval(query, user_id)
        return res

    async def get_lang_btn_status(self, user_id: int) -> str:
        """For handling LANG button under the comic"""
        query = """SELECT lang_btn_status FROM users
                   WHERE user_id = $1;"""

        res = await self.pool.fetchval(query, user_id)
        return res

    async def toggle_lang_btn_status(self, user_id: int):
        """For handling LANG button under the comic"""
        query = """UPDATE users 
                   SET lang_btn_status = NOT lang_btn_status 
                   WHERE user_id = $1;"""

        await self.pool.execute(query, user_id)

    async def toggle_only_ru_mode_status(self, user_id: int):
        query = """UPDATE users 
                   SET only_ru_mode = NOT only_ru_mode 
                   WHERE user_id = $1;"""

        await self.pool.execute(query, user_id)

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

    async def get_bookmarks(self, user_id: int) -> list[int]:
        query = """SELECT bookmarks FROM users
                   WHERE user_id = $1;"""

        res = await self.pool.fetchrow(query, user_id)
        return json.loads(res['bookmarks'])

    async def update_bookmarks(self, user_id: int, new_bookmarks: list[int]):
        query = """UPDATE users SET bookmarks = $1
                   WHERE user_id = $2;"""

        upd_bookmarks_json = json.dumps(new_bookmarks)
        await self.pool.execute(query, upd_bookmarks_json, user_id)

    """SUBSCRIPTION"""

    async def get_subscribed_users(self) -> tuple[int]:
        query = """SELECT array_agg(user_id) FROM users
                   WHERE is_subscribed = 1;"""

        res = await self.pool.fetchval(query)
        return tuple(res) if res else ()

    async def get_notification_sound_status(self, user_id: int) -> tuple[int]:
        query = """SELECT notification_sound_status FROM users
                   WHERE user_id = $1;"""

        res = await self.pool.fetchval(query, user_id)
        return res

    async def toggle_notification_sound_status(self, user_id: int):
        query = """UPDATE users 
                   SET notification_sound_status = NOT notification_sound_status 
                   WHERE user_id = $1;"""

        await self.pool.execute(query, user_id)


users_db = UsersDatabase()
