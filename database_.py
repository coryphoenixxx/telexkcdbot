import sqlite3 as sql
from parser_ import Parser


def create_users_database():
    create_users_table_query = """CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER UNIQUE,
        current_comic INTEGER DEFAULT 1,
        fav_comics JSON DEFAULT '[]',
        STATE TEXT DEFAULT 'default'
        )"""
    with sql.connect("users.db") as conn:
        cur = conn.cursor()
        cur.execute(create_users_table_query)


def add_new_user(user_id):
    add_new_user_query = f"""INSERT INTO users (user_id) VALUES({user_id})"""
    with sql.connect("users.db") as conn:
        cur = conn.cursor()
        cur.execute(add_new_user_query)


def get_user_current_comic(user_id):
    get_user_current_comic_query = f"""SELECT current_comic FROM users WHERE user_id == {user_id}"""
    with sql.connect("users.db") as conn:
        cur = conn.cursor()
        cur.execute(get_user_current_comic_query)
        result = cur.fetchone()[0]
        return result


def update_user_current_comic(user_id, new_current_comic):
    update_user_current_comic_query = f"""UPDATE users SET current_comic = {new_current_comic}
                                          WHERE user_id == {user_id}"""
    with sql.connect("users.db") as conn:
        cur = conn.cursor()
        cur.execute(update_user_current_comic_query)


def create_comics_database():
    create_comics_table_query = """CREATE TABLE IF NOT EXISTS comics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        comic_id INTEGER UNIQUE,
        title MESSAGE_TEXT ,
        img_url MESSAGE_TEXT,
        comment MESSAGE_TEXT,
        public_date DATE,
        rus_title MESSAGE_TEXT,
        rus_img_url MESSAGE_TEXT,
        rus_comment MESSAGE_TEXT,
        explain_text MESSAGE_TEXT
        )"""
    with sql.connect("comics.db") as conn:
        cur = conn.cursor()
        cur.execute(create_comics_table_query)


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
                             VALUES(?,?,?,?,?,?,?,?,?)"""
    with sql.connect("comics.db") as conn:
        cur = conn.cursor()
        cur.execute(add_new_user_query, comic_values)


if __name__ == "__main__":
    from concurrent.futures import ThreadPoolExecutor

    p = Parser()
    last = p.get_last_comic_number()

    create_comics_database()

    def parse_and_write_to_db(number):
        data = p.get_full_comic_data(number)
        comic_values = tuple(data.values())
        add_new_comic(comic_values)


    with ThreadPoolExecutor(max_workers=20) as executor:
        executor.map(parse_and_write_to_db, iter(range(1, last+1)))










