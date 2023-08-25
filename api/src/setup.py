from aiohttp import web
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from src.config import Config
from src.middlewares import db_session_middleware_factory
from src.router import router


def create_engine(config: Config) -> AsyncEngine:
    engine = create_async_engine(
        url=config.pg.postgres_dsn,
        echo=config.sqla.echo,
        echo_pool=config.sqla.echo,
        pool_size=config.sqla.pool_size,
        pool_pre_ping=True,
    )
    engine.connect()

    return engine


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(bind=engine, expire_on_commit=False)


def create_app(config: Config) -> web.Application:
    engine = create_engine(config)
    session_factory = create_session_factory(engine)

    app = web.Application(
        client_max_size=1024 ** 2 * 5,
        middlewares=[
            db_session_middleware_factory(session_factory),
        ])

    router.setup_routes(app)

    return app
