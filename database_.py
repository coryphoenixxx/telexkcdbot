import aiosqlite as aiosql
import json


class UsersDatabase:
    _db_path = "databases/users.db"

    async def create(self):
        query = """CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE,
            current_comic INTEGER DEFAULT 1,
            bookmarks JSON DEFAULT '[]',
            is_subscribed INTEGER DEFAULT 0, 
            state MESSAGE_TEXT DEFAULT 'default'
            );"""
        async with aiosql.connect(self._db_path) as db:
            await db.execute(query)
            await db.commit()

    """USER"""

    async def new_user(self, user_id):
        query = f"""INSERT or IGNORE INTO users (user_id)
                    VALUES({user_id});"""
        async with aiosql.connect(self._db_path) as db:
            await db.execute(query)
            await db.commit()

    async def get_cur_comic(self, user_id):
        query = f"""SELECT current_comic FROM users 
                    WHERE user_id == {user_id};"""
        async with aiosql.connect(self._db_path) as db:
            async with db.execute(query) as cur:
                res = await cur.fetchone()
                return res[0]

    async def update_cur_comic_id(self, user_id, new_current_comic):
        query = f"""UPDATE users SET current_comic = {new_current_comic}
                    WHERE user_id == {user_id};"""
        async with aiosql.connect(self._db_path) as db:
            await db.execute(query)
            await db.commit()

    """BOOKMARKS"""

    async def bookmarks(self, user_id):
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
                    return (id[0] for id in res)

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
    async def len(self):
        query = """SELECT COUNT (*) FROM users;"""
        async with aiosql.connect(self._db_path) as db:
            async with db.execute(query) as cur:
                res = await cur.fetchone()
                return res[0]


class ComicsDatabase:
    _db_path = "databases/comics.db"
    eng_cols = ('comic_id', 'title', 'img_url', 'comment', 'public_date', 'is_specific')
    rus_cols = ('comic_id', 'rus_title', 'rus_img_url', 'rus_comment', 'public_date', 'is_specific')

    async def create_comics_database(self):
        query = """CREATE TABLE IF NOT EXISTS comics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            comic_id INTEGER UNIQUE,
            title VARCHAR(128) DEFAULT '...',
            img_url VARCHAR(128) DEFAULT '',
            comment MESSAGE_TEXT DEFAULT '...',
            public_date DATE DEFAULT '',
            is_specific INTEGER DEFAULT 0,
            rus_title VARCHAR(128) DEFAULT '',
            rus_img_url VARCHAR(128) DEFAULT '',
            rus_comment MESSAGE_TEXT DEFAULT ''
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
                                       rus_title, 
                                       rus_img_url, 
                                       rus_comment
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
        title = title.strip()
        query = f"""SELECT comic_id FROM comics
                    WHERE title LIKE '%{title}%'
                    ORDER BY comic_id DESC;"""
        async with aiosql.connect(self._db_path) as db:
            async with db.execute(query) as cur:
                res = await cur.fetchall()
                if not res:
                    return None
                else:
                    return [el[0] for el in res]

    async def get_rus_version_data(self, comic_id):
        query = f"""SELECT comic_id, rus_title, rus_img_url, rus_comment, public_date, is_specific FROM comics
                    WHERE comic_id == {comic_id};"""
        async with aiosql.connect(self._db_path) as db:
            async with db.execute(query) as cur:
                res = await cur.fetchone()
                return dict(zip(self.rus_cols, res))

    async def get_last_comic_id(self):
        query = f"""SELECT comic_id FROM comics 
                    ORDER BY comic_id DESC;"""
        async with aiosql.connect(self._db_path) as db:
            async with db.execute(query) as cur:
                res = await cur.fetchone()
                return res[0]

    @property
    async def len(self):
        query = """SELECT COUNT (*) FROM comics;"""
        async with aiosql.connect(self._db_path) as db:
            async with db.execute(query) as cur:
                res = await cur.fetchone()
                return res[0]


if __name__ == "__main__":
    """FILL COMIC_DB"""
    import asyncio
    from concurrent.futures import ThreadPoolExecutor
    from parser_ import Parser

    parser = Parser()
    comics_db = ComicsDatabase()
    latest = parser.latest_comic_id
    comics_values = []


    async def parse(comic_id):
        data = await parser.get_full_comic_data(comic_id)
        comics_values.append(tuple(data.values()))


    async def write_to_db():
        await comics_db.create_comics_database()
        for val in comics_values:
            await comics_db.add_new_comic(val)

    # TODO: remake https://pymotw.com/3/asyncio/executors.html
    with ThreadPoolExecutor(max_workers=20) as executor:
        executor.map(parse, iter(range(1, latest + 1)))

    event_loop = asyncio.get_event_loop()
    event_loop.run_until_complete(write_to_db())
    event_loop.close()
