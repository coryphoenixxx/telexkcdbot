import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, declared_attr, mapped_column

from api.core.config import DbConfig, settings


class Base(DeclarativeBase):
    __abstract__ = True

    @declared_attr.directive
    def __tablename__(cls) -> str:
        return f"{cls.__name__.lower()}s"

    id: Mapped[int] = mapped_column(primary_key=True)


class Database:
    def __init__(self, config: DbConfig):
        self._config = config
        self._engine = self.create_engine(config)
        self._session_factory = self.create_session_factory(self._engine)

    @staticmethod
    def create_engine(config: DbConfig) -> AsyncEngine:
        return create_async_engine(
            url=config.pg.dsn,
            echo=config.sqla.echo,
            echo_pool=config.sqla.echo,
            pool_size=config.sqla.pool_size,
        )

    @staticmethod
    def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
        return async_sessionmaker(
            bind=engine,
            expire_on_commit=False,
        )

    def session_factory(self):
        yield self._session_factory

    async def connect(self):
        try:
            async with self._engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
        except ConnectionError as e:
            logging.fatal(f"Database connection failed! ERROR: {e.strerror}")

    async def disconnect(self):
        await self._engine.dispose()


db = Database(config=settings.db)
