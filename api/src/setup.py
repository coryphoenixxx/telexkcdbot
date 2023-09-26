
from aiohttp import web
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from src.config import Config
from src.middlewares import db_session_middleware_factory, error_middleware
from src.router import router
from src.services.converter_service import ConverterService
from src.services.image_service import ImageReaderService


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


async def create_app(config: Config) -> web.Application:
    engine = create_engine(config)
    session_factory = create_session_factory(engine)

    app = web.Application(
        client_max_size=config.api.client_max_size,
        middlewares=[
            error_middleware,
            db_session_middleware_factory(session_factory),
        ])

    router.setup_routes(app)

    ImageReaderService.setup(config)
    ConverterService.setup(config.img.converter_url)

    return app
