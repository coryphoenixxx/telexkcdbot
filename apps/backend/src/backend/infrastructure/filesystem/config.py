from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class FilesystemConfig:
    static_dir: Path
    temp_dir: Path
    prescraped_dir: Path
    upload_max_size: int
