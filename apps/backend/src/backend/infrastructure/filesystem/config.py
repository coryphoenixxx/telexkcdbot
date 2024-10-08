from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class FSConfig:
    root_dir: Path
