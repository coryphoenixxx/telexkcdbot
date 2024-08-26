from dataclasses import dataclass
from pathlib import Path


@dataclass
class APIConfig:
    host: str
    port: int
    static_dir: Path
    tmp_dir: Path
    upload_max_size: int
