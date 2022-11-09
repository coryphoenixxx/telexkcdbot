import asyncpg
from api_config import DATABASE_URL
from asyncpg.exceptions import ConnectionDoesNotExistError
from databases.comics import Comics
from databases.users import Users
from loguru import logger


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
                await _db.create_table()
        except (ConnectionDoesNotExistError, AttributeError, ValueError):
            logger.error("Pool was not created")

    @property
    def pool_size(self) -> int:
        pool_size: int = Database.pool.get_size()
        return pool_size


db = Database()
