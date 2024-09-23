from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class CLIConfig:
    prescraped_dir: Path
