import sqlite3 as sql


class UsersDatabase:
    @staticmethod
    def create_users_database():
        query = """CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE,
            current_comic INTEGER DEFAULT 1,
            fav_comics JSON DEFAULT '[]',
            subscribed INTEGER DEFAULT 0, 
            STATE MESSAGE_TEXT DEFAULT 'default'
            );"""
        with sql.connect("users.db") as conn:
            cur = conn.cursor()
            cur.execute(query)

    @staticmethod
    def add_new_user(user_id):
        add_new_user_query = f"""INSERT INTO users (user_id) VALUES({user_id});"""
        with sql.connect("users.db") as conn:
            cur = conn.cursor()
            cur.execute(add_new_user_query)

    @staticmethod
    def get_user_current_comic(user_id):
        query = f"""SELECT current_comic FROM users WHERE user_id == {user_id};"""
        with sql.connect("users.db") as conn:
            cur = conn.cursor()
            cur.execute(query)
            result = cur.fetchone()[0]
            return result

    @staticmethod
    def update_user_current_comic(user_id, new_current_comic):
        update_user_current_comic_query = f"""UPDATE users SET current_comic = {new_current_comic}
                                              WHERE user_id == {user_id};"""
        with sql.connect("users.db") as conn:
            cur = conn.cursor()
            cur.execute(update_user_current_comic_query)









class ComicsDatabase:
    @staticmethod
    def create_comics_database():
        create_comics_table_query = """CREATE TABLE IF NOT EXISTS comics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            comic_id INTEGER UNIQUE,
            title MESSAGE_TEXT DEFAULT '',
            img_url MESSAGE_TEXT DEFAULT '',
            comment MESSAGE_TEXT DEFAULT '',
            public_date DATE DEFAULT '',
            rus_title MESSAGE_TEXT DEFAULT '',
            rus_img_url MESSAGE_TEXT DEFAULT '',
            rus_comment MESSAGE_TEXT DEFAULT '',
            explain_text MESSAGE_TEXT DEFAULT '' #remove!!!
            );"""
        with sql.connect("comics.db") as conn:
            cur = conn.cursor()
            cur.execute(create_comics_table_query)

    @staticmethod
    def add_new_comic(comic_values):
        add_new_user_query = """INSERT INTO comics (comic_id, 
                                                    title, 
                                                    img_url, 
                                                    comment, 
                                                    public_date, 
                                                    rus_title, 
                                                    rus_img_url, 
                                                    rus_comment, 
                                                    explain_text)
                                 VALUES(?,?,?,?,?,?,?,?,?);"""
        with sql.connect("comics.db") as conn:
            cur = conn.cursor()
            cur.execute(add_new_user_query, comic_values)


    @staticmethod
    def get_original_comic_data(comic_id):
        query = f"""SELECT title, img_url, comment, public_date FROM comics WHERE comic_id == {comic_id};"""
        with sql.connect("comics.db") as conn:
            cur = conn.cursor()
            cur.execute(query)
            result = cur.fetchone()
            data = dict(zip(('title', 'img_url', 'comment', 'public_date'), result))
            return data

    @staticmethod
    def get_rus_version_data(comic_id):
        query = f"""SELECT rus_title, rus_img_url, rus_comment, public_date FROM comics WHERE comic_id == {comic_id};"""
        with sql.connect("comics.db") as conn:
            cur = conn.cursor()
            cur.execute(query)
            result = cur.fetchone()
            data = dict(zip(('rus_title', 'rus_img_url', 'rus_comment', 'public_date'), result))
            return data

    @staticmethod
    def get_explanation_data(comic_id):
        query = f"""SELECT explain_text FROM comics WHERE comic_id == {comic_id};"""
        with sql.connect("comics.db") as conn:
            cur = conn.cursor()
            cur.execute(query)
            result = cur.fetchone()[0]
            url = f'https://www.explainxkcd.com/{comic_id}'
            return result, url

    @staticmethod
    def get_last_comic_id():
        query = f"""SELECT comic_id FROM comics ORDER BY comic_id DESC;"""
        with sql.connect("comics.db") as conn:
            cur = conn.cursor()
            cur.execute(query)
            result = cur.fetchone()[0]
            return result


if __name__ == "__main__":
    # from parser_ import Parser
    #
    # p = Parser()
    # last = p.get_last_comic_number()
    #
    # comics_db = ComicsDatabase()
    # comics_db.create_comics_database()
    #
    # def parse_and_write_to_db(number):
    #     data = p.get_full_comic_data(number)
    #     comic_values = tuple(data.values())
    #     comics_db.add_new_comic(comic_values)
    #
    #
    # from concurrent.futures import ThreadPoolExecutor
    # with ThreadPoolExecutor(max_workers=20) as executor:
    #     executor.map(parse_and_write_to_db, iter(range(1, last+1)))

    db = ComicsDatabase()
    id = db.get_last_comic_id()
    print(id)










