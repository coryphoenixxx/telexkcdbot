import json
import asyncpg

from datetime import date, timedelta
from typing import Sequence

from telexkcdbot.models import MenuKeyboardInfo, AdminUsersInfo


class UsersDatabase:
    pool: asyncpg.Pool

    async def create(self, pool: asyncpg.Pool):
        self.pool = pool

        query = """CREATE TABLE IF NOT EXISTS users (
                     id SERIAL NOT NULL,
                     user_id INTEGER UNIQUE,
                     user_lang VARCHAR(2) DEFAULT 'en',
                     last_comic_info VARCHAR(10) DEFAULT '0_en', 
                     bookmarks JSON DEFAULT '[]',
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

    async def get_user_lang(self, user_id: int) -> str:
        query = """SELECT user_lang FROM users 
                   WHERE user_id = $1;"""

        return await self.pool.fetchval(query, user_id)

    async def set_user_lang(self, user_id: int, lang: str):
        query = """UPDATE users SET user_lang = $1, only_ru_mode=FALSE 
                   WHERE user_id = $2;"""

        await self.pool.execute(query, lang, user_id)

    async def get_last_comic_info(self, user_id: int) -> tuple[int, str]:
        query = """SELECT last_comic_info FROM users 
                   WHERE user_id = $1;"""

        res = await self.pool.fetchval(query, user_id)
        comic_id, comic_lang = res.split('_')
        return int(comic_id), comic_lang

    async def get_all_users_ids(self) -> Sequence[int]:
        query = """SELECT array_agg(user_id) FROM users;"""

        res = await self.pool.fetchval(query)
        return tuple(res) if res else ()

    async def get_only_ru_mode_status(self, user_id: int) -> bool:
        query = """SELECT only_ru_mode FROM users 
                   WHERE user_id = $1;"""

        return await self.pool.fetchval(query, user_id)

    async def get_ban_status(self, user_id: int) -> bool:
        query = """SELECT is_banned FROM users 
                   WHERE user_id = $1;"""

        return await self.pool.fetchval(query, user_id)

    async def ban_user(self, user_id: int):
        query = """UPDATE users SET is_banned = True
                   WHERE user_id = $1;"""

        await self.pool.execute(query, user_id)

    async def get_lang_btn_status(self, user_id: int) -> bool:
        """For handling LANG button under the comic"""
        query = """SELECT lang_btn_status FROM users
                   WHERE user_id = $1;"""

        return await self.pool.fetchval(query, user_id)

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

    async def update_last_comic_info(self, user_id: int, new_comic_id: int, new_comic_lang: str):
        query = """UPDATE users SET last_comic_info = $1
                   WHERE user_id = $2;"""

        last_comic_info = str(new_comic_id) + '_' + new_comic_lang
        await self.pool.execute(query, last_comic_info, user_id)

    async def update_last_action_date(self, user_id: int, action_date: date):
        query = """UPDATE users SET last_action_date = $1
                   WHERE user_id = $2;"""

        await self.pool.execute(query, action_date, user_id)

    async def get_admin_users_info(self) -> AdminUsersInfo:
        query = """SELECT COUNT(user_id), 
                          array_agg(last_action_date),
                          array_agg(only_ru_mode) FROM users;"""

        res = await self.pool.fetchrow(query)
        last_week_active_users_num = sum(((date.today() - d) < timedelta(days=7) for d in res[1]))
        return AdminUsersInfo(users_num=res[0],
                              last_week_active_users_num=last_week_active_users_num,
                              only_ru_users_num=sum(res[2]))

    async def get_user_menu_info(self, user_id: int) -> MenuKeyboardInfo:
        query = """SELECT user_lang, last_comic_info, lang_btn_status, notification_sound_status, only_ru_mode
                   FROM users
                   WHERE user_id = $1;"""

        res = await self.pool.fetchrow(query, user_id)
        return MenuKeyboardInfo(notification_sound_status=res['notification_sound_status'],
                                only_ru_mode_status=res['only_ru_mode'],
                                lang_btn_status=res['lang_btn_status'],
                                user_lang=res['user_lang'],
                                last_comic_id=int(res['last_comic_info'][0]))

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

    """NOTIFICATION"""

    async def get_notification_sound_status(self, user_id: int) -> bool:
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
