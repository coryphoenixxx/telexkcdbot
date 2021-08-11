import aiosqlite as aiosql
import json

from datetime import date, datetime, timedelta


class UsersDatabase:
    _db_path = "databases/users.db"

    async def create(self):
        query = f"""CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE,
            cur_comic_info VARCHAR(10) DEFAULT '0_en', 
            bookmarks JSON DEFAULT '[]',
            is_subscribed INTEGER DEFAULT 1, 
            user_lang VARCHAR(2) DEFAULT 'ru',
            last_action_date VARCHAR(10) DEFAULT '{str(date.today())}');"""
        async with aiosql.connect(self._db_path) as db:
            await db.execute(query)
            await db.commit()

    """USER"""

    async def add_user(self, user_id):
        query = f"""INSERT or IGNORE INTO users (user_id)
                    VALUES({user_id});"""
        async with aiosql.connect(self._db_path) as db:
            await db.execute(query)
            await db.commit()

    async def delete_user(self, user_id):
        query = f"""DELETE FROM users
                    WHERE user_id == {user_id};"""
        async with aiosql.connect(self._db_path) as db:
            await db.execute(query)
            await db.commit()

    async def get_cur_comic_info(self, user_id):
        query = f"""SELECT cur_comic_info FROM users 
                    WHERE user_id == {user_id};"""
        async with aiosql.connect(self._db_path) as db:
            async with db.execute(query) as cur:
                res = await cur.fetchone()
                comic_id, comic_lang = res[0].split('_')
                return int(comic_id), comic_lang

    async def get_all_users_ids(self):
        query = f"""SELECT user_id FROM users;"""
        async with aiosql.connect(self._db_path) as db:
            async with db.execute(query) as cur:
                res = await cur.fetchall()
                if not res:
                    return []
                else:
                    return [user_id[0] for user_id in res]

    async def get_user_lang(self, user_id):
        """FOR HANDLING RU BUTTON"""
        query = f"""SELECT user_lang FROM users
                    WHERE user_id == {user_id};"""
        async with aiosql.connect(self._db_path) as db:
            async with db.execute(query) as cur:
                res = await cur.fetchone()
                return res[0]

    async def set_user_lang(self, user_id, lang):
        """FOR HANDLING RU BUTTON"""
        query = f"""UPDATE users SET user_lang = '{lang}' 
                    WHERE user_id == {user_id};"""
        async with aiosql.connect(self._db_path) as db:
            await db.execute(query)
            await db.commit()

    async def update_cur_comic_info(self, user_id, new_current_comic_id, new_current_comic_lang='en'):
        new_info = str(new_current_comic_id) + '_' + new_current_comic_lang
        query = f"""UPDATE users SET cur_comic_info = '{new_info}'
                    WHERE user_id == {user_id};"""
        async with aiosql.connect(self._db_path) as db:
            await db.execute(query)
            await db.commit()

    async def update_last_action_date(self, user_id, date):
        query = f"""UPDATE users SET last_action_date = '{date}'
                    WHERE user_id == {user_id}"""
        async with aiosql.connect(self._db_path) as db:
            await db.execute(query)
            await db.commit()

    async def get_last_month_active_users(self):
        def less_month(dates_list):
            return sum([date.today() - date.fromisoformat(d) < timedelta(days=30) for d in dates_list])
        date_ = datetime.today().date()
        query = f"""SELECT last_action_date FROM users"""
        async with aiosql.connect(self._db_path) as db:
            async with db.execute(query) as cur:
                res = await cur.fetchall()
                active_users = [user_id[0] for user_id in res]
                return less_month(active_users)

    """BOOKMARKS"""

    async def get_bookmarks(self, user_id):
        query = f"""SELECT bookmarks FROM users 
                    WHERE user_id == {user_id};"""
        async with aiosql.connect(self._db_path) as db:
            async with db.execute(query) as cur:
                res = await cur.fetchone()
                return json.loads(res[0])

    async def update_bookmarks(self, user_id, new_bookmarks):
        new_bookmarks_json = json.dumps(new_bookmarks)
        query = f"""UPDATE users SET bookmarks = '{new_bookmarks_json}'
                    WHERE user_id == {user_id};"""
        async with aiosql.connect(self._db_path) as db:
            await db.execute(query)
            await db.commit()

    """SUBSCRIPTION"""

    @property
    async def subscribed_users(self):
        query = f"""SELECT user_id FROM users 
                    WHERE is_subscribed == 1;"""
        async with aiosql.connect(self._db_path) as db:
            async with db.execute(query) as cur:
                res = await cur.fetchall()
                if not res:
                    return []
                else:
                    return (user_id[0] for user_id in res)

    async def subscribe(self, user_id):
        query = f"""UPDATE users SET is_subscribed = 1
                    WHERE user_id == {user_id};"""
        async with aiosql.connect(self._db_path) as db:
            await db.execute(query)
            await db.commit()

    async def unsubscribe(self, user_id):
        query = f"""UPDATE users SET is_subscribed = 0
                    WHERE user_id == {user_id};"""
        async with aiosql.connect(self._db_path) as db:
            await db.execute(query)
            await db.commit()

    @property
    async def length(self):
        query = f"""SELECT COUNT (*) FROM users;"""
        async with aiosql.connect(self._db_path) as db:
            async with db.execute(query) as cur:
                res = await cur.fetchone()
                return res[0]


class ComicsDatabase:
    _db_path = "databases/comics.db"
    eng_cols = ('comic_id', 'title', 'img_url', 'comment', 'public_date', 'is_specific')
    ru_cols = ('comic_id', 'ru_title', 'ru_img_url', 'ru_comment', 'public_date', 'is_specific')

    async def create_comics_database(self):
        query = """CREATE TABLE IF NOT EXISTS comics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            comic_id INTEGER UNIQUE,
            title VARCHAR(128) DEFAULT '...',
            img_url VARCHAR(128) DEFAULT '',
            comment MESSAGE_TEXT DEFAULT '...',
            public_date DATE DEFAULT '',
            is_specific INTEGER DEFAULT 0,
            ru_title VARCHAR(128) DEFAULT '...',
            ru_img_url VARCHAR(128) DEFAULT '...',
            ru_comment MESSAGE_TEXT DEFAULT '...'
            );"""
        async with aiosql.connect(self._db_path) as db:
            await db.execute(query)
            await db.commit()

    async def add_new_comic(self, comic_values):
        query = """INSERT INTO comics (comic_id, 
                                       title, 
                                       img_url, 
                                       comment, 
                                       public_date,
                                       is_specific, 
                                       ru_title, 
                                       ru_img_url, 
                                       ru_comment
                                       )
                    VALUES(?,?,?,?,?,?,?,?,?);"""
        async with aiosql.connect(self._db_path) as db:
            await db.execute(query, comic_values)
            await db.commit()

    async def get_comic_data_by_id(self, comic_id):
        query = f"""SELECT comic_id, title, img_url, comment, public_date, is_specific FROM comics
                    WHERE comic_id == {comic_id};"""
        async with aiosql.connect(self._db_path) as db:
            async with db.execute(query) as cur:
                res = await cur.fetchone()
                return dict(zip(self.eng_cols, res))

    async def get_comics_ids_by_title(self, title):
        query = f"""SELECT comic_id FROM comics
                    WHERE title LIKE '% {title} %'
                    OR title LIKE '%{title} %'
                    OR title LIKE '% {title}%'
                    OR title = '{title}'
                    OR ru_title LIKE '% {title} %'
                    OR ru_title LIKE '%{title} %'
                    OR ru_title LIKE '% {title}%'
                    OR ru_title = '{title}'
                    ORDER BY comic_id;"""
        async with aiosql.connect(self._db_path) as db:
            async with db.execute(query) as cur:
                res = await cur.fetchall()
                if not res:
                    return None
                else:
                    return [el[0] for el in res]

    async def get_ru_comic_data_by_id(self, comic_id):
        query = f"""SELECT comic_id, ru_title, ru_img_url, ru_comment, public_date, is_specific FROM comics
                    WHERE comic_id == {comic_id};"""
        async with aiosql.connect(self._db_path) as db:
            async with db.execute(query) as cur:
                res = await cur.fetchone()
                return dict(zip(self.ru_cols, res))

    async def get_last_comic_id(self):
        query = f"""SELECT comic_id FROM comics 
                    ORDER BY comic_id DESC;"""
        async with aiosql.connect(self._db_path) as db:
            async with db.execute(query) as cur:
                res = await cur.fetchone()
                return res[0]

    async def change_spec_status(self, comic_id):
        get_query = f"""SELECT is_specific FROM comics
                        WHERE comic_id == {comic_id};"""
        set_query = """UPDATE comics SET is_specific = {value} /* not a bug */
                       WHERE comic_id == {comic_id};"""
        async with aiosql.connect(self._db_path) as db:
            async with db.execute(get_query) as cur:
                res = await cur.fetchone()
                cur_value = res[0]
                await db.execute(set_query.format(value=int(not cur_value), comic_id=comic_id))
                await db.commit()

    @property
    async def length(self):
        query = """SELECT COUNT (*) FROM comics;"""
        async with aiosql.connect(self._db_path) as db:
            async with db.execute(query) as cur:
                res = await cur.fetchone()
                return res[0]


if __name__ == "__main__":

    """FILL COMIC_DB"""

    import asyncio
    from tqdm import trange
    from xkcd_parser import Parser

    parser = Parser()
    comics_db = ComicsDatabase()
    latest = parser.actual_latest_comic_id
    comics_values = []

    async def parse():
        print('Parsing:')
        for comic_id in trange(1, latest + 1):
            data = await parser.get_full_comic_data(comic_id)
            comics_values.append(tuple(data.values()))

    async def write_to_db():
        await comics_db.create_comics_database()
        print('Writing...')
        for val in comics_values:
            await comics_db.add_new_comic(val)


    event_loop = asyncio.get_event_loop()
    event_loop.run_until_complete(parse())
    event_loop.run_until_complete(write_to_db())
    event_loop.close()
