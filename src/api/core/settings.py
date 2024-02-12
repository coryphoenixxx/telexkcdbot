from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class DBConfig(BaseModel):
    driver: str
    host: str
    port: int
    user: str
    password: str
    dbname: str

    @property
    def dsn(self):
        return (
            f"postgresql+{self.driver}://"
            f"{self.user}:{self.password}@{self.host}:{self.port}/{self.dbname}"
        )


class SQLAConfig(BaseModel):
    pool_size: int
    echo: bool = True


class DbConfig(BaseModel):
    pg: DBConfig
    sqla: SQLAConfig


class AppConfig(BaseModel):
    docs_url: str = "/docs"
    redoc_url: str = "/redoc"
    openapi_url: str = "/openapi.json"
    debug: bool = True
    upload_max_size: str = "1024**2*10"
    tmp_dir: Path
    static_dir: Path


class Environment(StrEnum):
    DEV = "DEV"
    PROD = "PROD"


class Settings(BaseSettings):
    db: DbConfig
    app: AppConfig
    env: Environment = Environment.DEV

    model_config = SettingsConfigDict(
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra='ignore',
    )


def load_settings():
    settings = Settings()

    if settings.env is Environment.PROD:
        settings.db.sqla.echo = False
        settings.app.debug = False
        settings.app.docs_url = None
        settings.app.redoc_url = None
        settings.app.openapi_url = None

    return settings
