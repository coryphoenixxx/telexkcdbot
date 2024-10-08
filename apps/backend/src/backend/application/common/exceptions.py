from dataclasses import dataclass

from backend.domain.exceptions import BaseAppError
from backend.domain.value_objects import TempFileUUID


@dataclass(slots=True)
class TempFileNotFoundError(BaseAppError):
    temp_file_id: TempFileUUID

    @property
    def message(self) -> str:
        return f"Temp file (id={self.temp_file_id.value}) not found."
