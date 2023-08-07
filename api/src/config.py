from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=Path(__file__).parent.parent / '.env',
        env_file_encoding='utf-8',
    )

    pg_driver: str
    pg_host: str
    pg_port: int
    pg_user: str
    pg_password: str
    pg_db: str

    sqla_echo: bool
    sqla_pool_size: int

    api_port: int
