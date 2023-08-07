from pathlib import Path

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class PG(BaseModel):
    driver: str
    host: str
    port: int
    user: str
    password: str
    db: str


class SQLA(BaseModel):
    echo: bool
    pool_size: int


class Config(BaseSettings):
    pg: PG
    sqla: SQLA
    api_port: int

    model_config = SettingsConfigDict(
        env_file=Path(__file__).parent.parent / '.env',
        env_file_encoding='utf-8',
        env_nested_delimiter='__',
    )
