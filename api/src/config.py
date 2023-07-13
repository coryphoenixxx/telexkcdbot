from dataclasses import dataclass

from decouple import config


@dataclass
class DbConfig:
    postgres_dsn: str
    sqla_echo: bool


@dataclass
class Config:
    db: DbConfig
    api_port: str


def load_config():
    user = config('DB_USER', default='postgres')
    password = config('DB_PASS', default='postgres')
    hostname = config('DB_HOST', default='localhost')
    port = config('DB_PORT', default='5432')
    database = config('DB_NAME', default='telexkcdbot')

    sqla_echo = config('SQLA_ECHO', default=False, cast=bool)

    api_port = config('API_PORT')

    return Config(
        db=DbConfig(
            postgres_dsn=f"postgresql+asyncpg://{user}:{password}@{hostname}:{port}/{database}",
            sqla_echo=sqla_echo,
        ),
        api_port=api_port,
    )
