from dataclasses import dataclass
from pathlib import Path

from backend.application.common.exceptions import BaseAppError
from backend.core.value_objects import TranslationImageID


@dataclass(slots=True)
class TranslationImageNotFoundError(BaseAppError):
    image_id: TranslationImageID

    @property
    def message(self) -> str:
        return f"Translation image (id={self.image_id.value}) not found."


@dataclass(slots=True)
class TempImageNotFoundError(BaseAppError):
    temp_image_id: str

    @property
    def message(self) -> str:
        return f"A temp image (id=`{self.temp_image_id}`) not found."


@dataclass(slots=True)
class ImageConversionError(BaseAppError):
    path: Path
    reason: str

    @property
    def message(self) -> str:
        return f"The image (name={self.path.name}) was not converted. Reason: `{self.reason}`"
