from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path


class FileStorageType(StrEnum):
    FS = "fs"
    S3 = "s3"


@dataclass(slots=True)
class AppConfig:
    upload_max_size: int  # TODO: move to image context?
    file_storage: FileStorageType  # TODO: move files context?
    temp_dir: Path
