from dataclasses import dataclass, field
from pathlib import Path

from api.infrastructure.database.config import DBConfig


@dataclass
class APIConfig:
    static_dir: Path
    tmp_dir: Path
    upload_max_size: int
    debug: bool = True
    docs_url: str = "/docs"
    redoc_url: str = "/redoc"
    openapi_url: str = "/openapi.json"


@dataclass
class AppConfig:
    db: DBConfig = field(default_factory=DBConfig)
    api: APIConfig = field(default_factory=APIConfig)
