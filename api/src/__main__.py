from aiohttp import web
from sqlalchemy import URL
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from src.config import Config
from src.router import router


def setup(config: Config):
    app = web.Application()

    postgres_dsn = URL.create(
        drivername=config.pg_driver,
        username=config.pg_user,
        password=config.pg_password,
        host=config.pg_host,
        port=config.pg_port,
        database=config.pg_db,
    )

    engine = create_async_engine(
        url=postgres_dsn,
        echo=config.sqla_echo,
        echo_pool=config.sqla_echo,
        pool_size=config.sqla_pool_size,
    )

    app.session_factory = async_sessionmaker(bind=engine)

    router.setup_routes(app)

    return app


def run_app():
    config = Config()
    app = setup(config)
    web.run_app(app, port=config.api_port)


if __name__ == "__main__":
    run_app()
