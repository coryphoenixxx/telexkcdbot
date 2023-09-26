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

    @property
    def postgres_dsn(self):
        return f"postgresql+{self.driver}://{self.user}:{self.password}@{self.host}:{self.port}/{self.db}"


class SQLA(BaseModel):
    echo: bool
    pool_size: int


class IMG(BaseModel):
    converter_url: str
    images_dir: str
    supported_extensions: str
    image_max_size: int

    def __init__(self, **kwargs):
        kwargs['image_max_size'] = eval(kwargs['image_max_size'])
        super().__init__(**kwargs)


class API(BaseModel):
    port: int
    client_max_size: int

    def __init__(self, **kwargs):
        kwargs['client_max_size'] = eval(kwargs['client_max_size'])
        super().__init__(**kwargs)


class Config(BaseSettings):
    pg: PG
    sqla: SQLA
    img: IMG
    api: API

    model_config = SettingsConfigDict(
        env_file=Path(__file__).parent.parent / '.env',
        env_file_encoding='utf-8',
        env_nested_delimiter='__',
    )
