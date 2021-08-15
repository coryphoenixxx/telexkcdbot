import asyncpg
import json

from datetime import date, timedelta

from config import DATABASE_URL


async def create_pool() -> asyncpg.Pool:
    return await asyncpg.create_pool(DATABASE_URL)


class UsersDatabase:
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool

    @staticmethod
    async def create():
        query = f"""CREATE TABLE IF NOT EXISTS users (
                      id SERIAL NOT NULL,
                      user_id INTEGER UNIQUE,
                      cur_comic_info VARCHAR(10) DEFAULT '0_en', 
                      bookmarks JSON DEFAULT '[]',
                      is_subscribed INTEGER DEFAULT 1, 
                      user_lang VARCHAR(2) DEFAULT 'ru',
                      last_action_date DATE DEFAULT CURRENT_DATE);                    

                    CREATE UNIQUE INDEX IF NOT EXISTS user_id_uindex ON users (id);"""

        conn: asyncpg.Connection = await asyncpg.connect(DATABASE_URL)
        await conn.execute(query)
        await conn.close()

    """USER"""

    async def add_user(self, user_id: int):
        query = f"""INSERT INTO users (user_id)
                    VALUES({user_id})
                    ON CONFLICT (user_id) DO NOTHING;"""
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute(query)

    async def delete_user(self, user_id: int):
        query = f"""DELETE FROM users
                    WHERE user_id = {user_id};"""
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute(query)

    async def get_cur_comic_info(self, user_id: int) -> (int, str):
        query = f"""SELECT cur_comic_info FROM users 
                    WHERE user_id = {user_id};"""
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                res = await conn.fetchval(query)

        comic_id, comic_lang = res.split('_')
        return int(comic_id), comic_lang

    @property
    async def all_users_ids(self) -> tuple:
        query = f"""SELECT array_agg(user_id) FROM users;"""
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                res = await conn.fetchval(query)
        return tuple(res) if res else ()

    async def get_user_lang(self, user_id):
        """For handling LANG button"""
        query = f"""SELECT user_lang FROM users
                    WHERE user_id = {user_id};"""
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                res = await conn.fetchval(query)
        return res

    async def set_user_lang(self, user_id: int, lang: str):
        """For handling LANG button"""
        query = f"""UPDATE users SET user_lang = '{lang}'
                    WHERE user_id = {user_id};"""
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute(query)

    async def update_cur_comic_info(self, user_id: int, new_cur_comic_id: int, new_cur_comic_lang: str):
        new_info = str(new_cur_comic_id) + '_' + new_cur_comic_lang
        query = f"""UPDATE users SET cur_comic_info = '{new_info}'
                    WHERE user_id = {user_id};"""
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute(query)

    async def update_last_action_date(self, user_id: int, action_date: date):
        query = f"""UPDATE users SET last_action_date = '{action_date}'
                    WHERE user_id = {user_id};"""
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute(query)

    async def get_last_month_active_users_num(self) -> int:
        def less_month(dates: list) -> int:
            return sum(((date.today() - d) < timedelta(days=30) for d in dates))

        query = f"""SELECT array_agg(last_action_date) FROM users;"""
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                res = await conn.fetchval(query)
        return less_month(res)

    """BOOKMARKS"""

    async def get_bookmarks(self, user_id: int) -> list:
        query = f"""SELECT bookmarks FROM users
                    WHERE user_id = {user_id};"""
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                res = await conn.fetchval(query)
        return json.loads(res)

    async def update_bookmarks(self, user_id: int, new_bookmarks: list):
        new_bookmarks_json = json.dumps(new_bookmarks)
        query = f"""UPDATE users SET bookmarks = '{new_bookmarks_json}'
                    WHERE user_id = {user_id};"""
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute(query)

    """SUBSCRIPTION"""

    @property
    async def subscribed_users(self) -> (tuple, None):
        query = f"""SELECT array_agg(user_id) FROM users
                    WHERE is_subscribed = 1;"""
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                res = await conn.fetchval(query)
            return tuple(res) if res else ()

    async def change_subscription_status(self, user_id: int):
        get_query = f"""SELECT is_subscribed FROM users
                        WHERE user_id = {user_id};"""
        set_query = """UPDATE users SET is_subscribed = {value} /* not a bug */
                       WHERE user_id = {user_id};"""
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                cur_value = await conn.fetchval(get_query)
                await conn.execute(set_query.format(value=int(not cur_value), user_id=user_id))


class ComicsDatabase:
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool

    @staticmethod
    async def create():
        query = """CREATE TABLE IF NOT EXISTS comics (
                        id SERIAL NOT NULL,
                        comic_id INTEGER NOT NULL UNIQUE,
                        title VARCHAR(128) DEFAULT '...',
                        img_url VARCHAR(128) DEFAULT '',
                        comment TEXT DEFAULT '...',
                        public_date DATE NOT NULL DEFAULT CURRENT_DATE,
                        is_specific INTEGER NOT NULL DEFAULT 0,
                        ru_title VARCHAR(128) DEFAULT '...',
                        ru_img_url VARCHAR(128) DEFAULT '...',
                        ru_comment TEXT DEFAULT '...');
    
                CREATE UNIQUE INDEX IF NOT EXISTS comic_id_uindex ON comics (comic_id);"""

        conn: asyncpg.Connection = await asyncpg.connect(DATABASE_URL)
        await conn.execute(query)
        await conn.close()

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
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute(query, *comic_values)

    @property
    async def all_comics_ids(self) -> tuple:
        query = f"""SELECT array_agg(comic_id) FROM comics;"""
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                res = await conn.fetchval(query)
        return tuple(res) if res else ()

    @property
    async def latest_comic_id(self) -> int:
        query = f"""SELECT comic_id FROM comics
                        ORDER BY comic_id DESC;"""
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                return await conn.fetchval(query)

    async def get_comic_data_by_id(self, comic_id: int) -> tuple:
        query = f"""SELECT comic_id, title, img_url, comment, public_date, is_specific
                    FROM comics
                    WHERE comic_id = {comic_id};"""
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                res = await conn.fetchrow(query)
        return tuple(res)

    async def get_ru_comic_data_by_id(self, comic_id: int) -> tuple:
        query = f"""SELECT comic_id, ru_title, ru_img_url, ru_comment, public_date, is_specific
                    FROM comics
                    WHERE comic_id = {comic_id};"""
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                res = await conn.fetchrow(query)
        return tuple(res)

    async def get_comics_info_by_title(self, title: str) -> list:
        query = f"""SELECT array_agg(comic_id), array_agg(title), array_agg(ru_title) FROM comics

                    WHERE title = '{title}'
                    OR title ILIKE '% {title}%'
                    OR title ILIKE '{title}%'
                    OR title ILIKE '%{title} %'
                    OR title ILIKE '%{title}'

                    OR ru_title = '{title}'
                    OR ru_title ILIKE '% {title}%'
                    OR ru_title ILIKE '{title}%'
                    OR ru_title ILIKE '%{title} %'
                    OR ru_title ILIKE '%{title}';"""

        async with self.pool.acquire() as conn:
            async with conn.transaction():
                res = await conn.fetchrow(query)
        if not res[0]:
            return []
        else:
            ids = res[0]
            titles = res[1]
            ru_titles = res[2]
            z = zip(ids, titles, ru_titles)
            info = [(_id, title, ru_title) for _id, title, ru_title in sorted(z, key=lambda x: len(x[1]))]
            return list(zip(*info))

    async def change_spec_status(self, comic_id: int):
        get_query = f"""SELECT is_specific FROM comics
                        WHERE comic_id = {comic_id};"""
        set_query = """UPDATE comics SET is_specific = {value} /* not a bug */
                       WHERE comic_id = {comic_id};"""
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                cur_value = await conn.fetchval(get_query)
                await conn.execute(set_query.format(value=int(not cur_value), comic_id=comic_id))


if __name__ == "__main__":
    # needs envs
    import asyncio
    from funcs import fill_comic_db

    loop = asyncio.get_event_loop()
    loop.run_until_complete(fill_comic_db())
