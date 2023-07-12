from dataclasses import dataclass
from decouple import config


@dataclass
class Config:
    postgres_dsn: str
    api_port: str


def load_config():
    user = config('DB_USER', default='postgres')
    password = config('DB_PASS', default='postgres')
    hostname = config('DB_HOST', default='localhost')
    port = config('DB_PORT', default='5432')
    database = config('DB_NAME', default='telexkcdbot')

    api_port = config('API_PORT')

    return Config(
        postgres_dsn=f"postgresql+asyncpg://{user}:{password}@{hostname}:{port}/{database}",
        api_port=api_port
    )
