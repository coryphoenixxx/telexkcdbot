from dataclasses import dataclass
from pathlib import Path


@dataclass
class APIConfig:
    static_dir: Path
    tmp_dir: Path
    upload_max_size: int
