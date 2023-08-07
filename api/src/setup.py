from aiohttp import web
from sqlalchemy import URL
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from src.config import Config
from src.router import router


def create_postgres_dsn(
        driver: str,
        user: str,
        password: str,
        host: str,
        port: int,
        db: str,
) -> str:
    postgres_dsn = URL.create(
        drivername='postgresql+' + driver,
        username=user,
        password=password,
        host=host,
        port=port,
        database=db,
    )

    return str(postgres_dsn)


def create_engine(config: Config):
    engine = create_async_engine(
        url=create_postgres_dsn(**config.pg.model_dump()),
        echo=config.sqla.echo,
        echo_pool=config.sqla.echo,
        pool_size=config.sqla.pool_size,
        pool_pre_ping=True,
    )

    return engine


def setup(config: Config):
    app = web.Application()

    engine = create_engine(config)
    engine.connect()

    app.session_factory = async_sessionmaker(bind=engine)

    router.setup_routes(app)

    return app
