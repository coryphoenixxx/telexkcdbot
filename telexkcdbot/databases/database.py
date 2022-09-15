import asyncpg

from telexkcdbot.config import DATABASE_URL
from telexkcdbot.databases.comics import Comics
from telexkcdbot.databases.users import Users


class Database:
    _pool = None

    def __init__(self):
        self.users = Users()
        self.comics = Comics()

    async def create(self):
        # TODO: ?sslmode=require for db_url
        # TODO: Exception
        Database._pool = await asyncpg.create_pool(DATABASE_URL, max_size=40, command_timeout=60)
        for child_db in self.__dict__.values():
            child_db.pool = Database._pool
            await child_db.create_table()

    @property
    def pool_size(self):
        return Database._pool.get_size()


db = Database()
