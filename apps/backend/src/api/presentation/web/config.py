from dataclasses import dataclass
from pathlib import Path


@dataclass
class APIConfig:
    static_dir: Path
    tmp_dir: Path
    upload_max_size: int
    debug: bool = True
    docs_url: str = "/docs"
    redoc_url: str = "/redoc"
    openapi_url: str = "/openapi.json"
