import aiosqlite as sql


users_db_filename = "users.db"
comics_db_filename = "comics.db"


class UsersDatabase:
    @staticmethod
    async def create_users_database():
        query = """CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE,
            current_comic INTEGER DEFAULT 1,
            fav_comics JSON DEFAULT '[]',
            subscribed INTEGER DEFAULT 0, 
            state MESSAGE_TEXT DEFAULT 'default'
            );"""
        async with sql.connect(users_db_filename) as db:
            await db.execute(query)
            await db.commit()

    @staticmethod
    async def add_new_user(user_id):
        query = f"""INSERT or IGNORE INTO users (user_id) VALUES({user_id});"""
        async with sql.connect(users_db_filename) as db:
            await db.execute(query)
            await db.commit()

    @staticmethod
    async def get_user_current_comic(user_id):
        query = f"""SELECT current_comic FROM users 
                    WHERE user_id == {user_id};"""
        async with sql.connect(users_db_filename) as db:
            async with db.execute(query) as cur:
                res = await cur.fetchone()
                return res[0]

    @staticmethod
    async def update_user_current_comic(user_id, new_current_comic):
        query = f"""UPDATE users SET current_comic = {new_current_comic}
                    WHERE user_id == {user_id};"""
        async with sql.connect(users_db_filename) as db:
            await db.execute(query)
            await db.commit()

    def __len__(self):
        query = """SELECT COUNT (*) FROM users"""
        with sql.connect(users_db_filename) as conn:
            cur = conn.cursor()
            cur.execute(query)
            return cur.fetchone()[0]


class ComicsDatabase:
    @staticmethod
    async def create_comics_database():
        query = """CREATE TABLE IF NOT EXISTS comics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            comic_id INTEGER UNIQUE,
            title MESSAGE_TEXT DEFAULT '',
            img_url MESSAGE_TEXT DEFAULT '',
            comment MESSAGE_TEXT DEFAULT '',
            public_date DATE DEFAULT '',
            rus_title MESSAGE_TEXT DEFAULT '',
            rus_img_url MESSAGE_TEXT DEFAULT '',
            rus_comment MESSAGE_TEXT DEFAULT ''
            );"""
        async with sql.connect(comics_db_filename) as db:
            await db.execute(query)
            await db.commit()

    @staticmethod
    async def add_new_comic(comic_values):
        query = """INSERT INTO comics (comic_id, 
                                       title, 
                                       img_url, 
                                       comment, 
                                       public_date, 
                                       rus_title, 
                                       rus_img_url, 
                                       rus_comment)
                    VALUES(?,?,?,?,?,?,?,?);"""
        async with sql.connect(comics_db_filename) as db:
            await db.execute(query, comic_values)
            await db.commit()

    @staticmethod
    async def get_comic_data_by_id(comic_id):
        query = f"""SELECT comic_id, title, img_url, comment, public_date FROM comics WHERE comic_id == {comic_id};"""
        async with sql.connect(comics_db_filename) as db:
            async with db.execute(query) as cur:
                result = await cur.fetchone()
                data = dict(zip(('comic_id', 'title', 'img_url', 'comment', 'public_date'), result))
                return data

    @staticmethod
    async def get_comic_data_by_title(title):
        title = title.strip()
        query = f"""SELECT comic_id, title, img_url, comment, public_date FROM comics WHERE title LIKE '%{title}%';"""
        async with sql.connect(comics_db_filename) as db:
            async with db.execute(query) as cur:
                result = await cur.fetchone()
                try:
                    data = dict(zip(('comic_id', 'title', 'img_url', 'comment', 'public_date'), result))
                except TypeError:
                    data = None
                return data

    @staticmethod
    async def get_rus_version_data(comic_id):
        query = f"""SELECT comic_id, rus_title, rus_img_url, rus_comment, public_date FROM comics WHERE comic_id == {comic_id};"""
        async with sql.connect(comics_db_filename) as db:
            async with db.execute(query) as cur:
                result = await cur.fetchone()
                data = dict(zip(('comic_id', 'rus_title', 'rus_img_url', 'rus_comment', 'public_date'), result))
                return data

    @staticmethod
    async def get_last_comic_id():
        query = f"""SELECT comic_id FROM comics ORDER BY comic_id DESC;"""
        async with sql.connect(comics_db_filename) as db:
            async with db.execute(query) as cur:
                res = await cur.fetchone()
                return res[0]

    def __len__(self):
        query = """SELECT COUNT (*) FROM comics"""
        with sql.connect(comics_db_filename) as conn:
            cur = conn.cursor()
            cur.execute(query)
            return cur.fetchone()[0]


if __name__ == "__main__":
    pass
    import pprint

    # from parser_ import Parser

    # parser = Parser()
    # latest = parser.get_and_update_latest_comic_id()

    # db.create_comics_database()

    # def parse_and_write_to_db(comic_id):
    #     data = parser.get_full_comic_data(comic_id)
    #     comic_values = tuple(data.values())
    #     comics_db.add_new_comic(comic_values)
    #
    #
    # from concurrent.futures import ThreadPoolExecutor
    # with ThreadPoolExecutor(max_workers=20) as executor:
    #     executor.map(parse_and_write_to_db, iter(range(1, latest)))

    # db = ComicsDatabase()














