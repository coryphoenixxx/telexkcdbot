from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path


class FileStorageType(StrEnum):
    FS = "fs"
    S3 = "s3"


@dataclass(slots=True)
class AppConfig:
    upload_max_size: int
    file_storage: FileStorageType
    temp_dir: Path
