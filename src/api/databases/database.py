import asyncpg
from asyncpg.exceptions import ConnectionDoesNotExistError
from loguru import logger

from api.config import DATABASE_URL
from api.databases.comics import Comics
from api.databases.users import Users


class Database:
    pool: asyncpg.Pool

    def __init__(self) -> None:
        self.users = Users()
        self.comics = Comics()

    async def create(self) -> None:
        # TODO: ?sslmode=require for db_url

        try:
            Database.pool = await asyncpg.create_pool(DATABASE_URL, max_size=40, command_timeout=60)

            for _db in self.__dict__.values():
                _db.pool = Database.pool
        except (ConnectionDoesNotExistError, AttributeError, ValueError):
            logger.error("Pool was not created")

    @property
    def pool_size(self) -> int:
        pool_size: int = Database.pool.get_size()
        return pool_size


db = Database()
