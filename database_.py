import aiosqlite as sql


class UsersDatabase:
    _db_path = "databases/users.db"

    async def create_users_database(self):
        query = """CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE,
            current_comic INTEGER DEFAULT 1,
            fav_comics JSON DEFAULT '[]',
            subscribed INTEGER DEFAULT 0, 
            state MESSAGE_TEXT DEFAULT 'default'
            );"""
        async with sql.connect(self._db_path) as db:
            await db.execute(query)
            await db.commit()

    async def add_new_user(self, user_id):
        query = f"""INSERT or IGNORE INTO users (user_id)
                    VALUES({user_id});"""
        async with sql.connect(self._db_path) as db:
            await db.execute(query)
            await db.commit()

    async def get_user_current_comic(self, user_id):
        query = f"""SELECT current_comic FROM users 
                    WHERE user_id == {user_id};"""
        async with sql.connect(self._db_path) as db:
            async with db.execute(query) as cur:
                res = await cur.fetchone()
                return res[0]

    async def get_subscribed_users(self):
        query = f"""SELECT user_id FROM users 
                    WHERE subscribed == 1;"""
        async with sql.connect(self._db_path) as db:
            async with db.execute(query) as cur:
                res = await cur.fetchall()
                return res

    async def update_user_current_comic(self, user_id, new_current_comic):
        query = f"""UPDATE users SET current_comic = {new_current_comic}
                    WHERE user_id == {user_id};"""
        async with sql.connect(self._db_path) as db:
            await db.execute(query)
            await db.commit()

    def __len__(self):
        query = """SELECT COUNT (*) FROM users"""
        with sql.connect(self._db_path) as conn:
            cur = conn.cursor()
            cur.execute(query)
            return cur.fetchone()[0]


class ComicsDatabase:
    db_path = "databases/comics.db"

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
        async with sql.connect(self.db_path) as db:
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
        async with sql.connect(self.db_path) as db:
            await db.execute(query, comic_values)
            await db.commit()

    async def get_comic_data_by_id(self, comic_id):
        query = f"""SELECT comic_id, title, img_url, comment, public_date, is_specific FROM comics
                    WHERE comic_id == {comic_id};"""
        async with sql.connect(self.db_path) as db:
            async with db.execute(query) as cur:
                res = await cur.fetchone()
                return dict(zip(('comic_id', 'title', 'img_url', 'comment', 'public_date', 'is_specific'), res))

    async def get_comics_by_title(self, title):
        title = title.strip()
        query = f"""SELECT comic_id, title, img_url, comment, public_date, is_specific FROM comics
                    WHERE title LIKE '%{title}%'
                    ORDER BY comic_id DESC;"""
        async with sql.connect(self.db_path) as db:
            async with db.execute(query) as cur:
                res = await cur.fetchall()
                if not res:
                    return None
                else:
                    entries = []
                    for entry in res:
                        d = dict(zip(('comic_id', 'title', 'img_url', 'comment', 'public_date', 'is_specific'), entry))  # TODO: remove from here
                        entries.append(d)
                    return entries

    async def get_rus_version_data(self, comic_id):
        query = f"""SELECT comic_id, rus_title, rus_img_url, rus_comment, public_date FROM comics
                    WHERE comic_id == {comic_id};"""
        async with sql.connect(self.db_path) as db:
            async with db.execute(query) as cur:
                res = await cur.fetchone()
                return dict(zip(('comic_id', 'rus_title', 'rus_img_url', 'rus_comment', 'public_date', 'is_specific'), res))

    async def get_last_comic_id(self):
        query = f"""SELECT comic_id FROM comics 
                    ORDER BY comic_id DESC;"""
        async with sql.connect(self.db_path) as db:
            async with db.execute(query) as cur:
                res = await cur.fetchone()
                return res[0]

    def __len__(self):
        query = """SELECT COUNT (*) FROM comics"""
        with sql.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(query)
            return cur.fetchone()[0]


if __name__ == "__main__":

    import asyncio
    from concurrent.futures import ThreadPoolExecutor
    from parser_ import Parser

    parser = Parser()
    comics_db = ComicsDatabase()
    latest = parser.get_and_update_latest_comic_id()
    comics_values = []

    def parse(comic_id):
        data = parser.get_full_comic_data(comic_id)
        comics_values.append(tuple(data.values()))

    async def write_to_db():
        await comics_db.create_comics_database()
        for val in comics_values:
            await comics_db.add_new_comic(val)


    with ThreadPoolExecutor(max_workers=20) as executor:
        executor.map(parse, iter(range(1, latest+1)))

    event_loop = asyncio.get_event_loop()
    event_loop.run_until_complete(write_to_db())
    event_loop.close()
