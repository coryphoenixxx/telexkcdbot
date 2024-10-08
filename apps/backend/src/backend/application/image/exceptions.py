from dataclasses import dataclass
from pathlib import Path

from backend.domain.exceptions import BaseAppError
from backend.domain.value_objects import ImageId


@dataclass(slots=True)
class ImageSizeExceededLimitError(BaseAppError):
    limit: int

    @property
    def message(self) -> str:
        return f"Image file size exceeded limit ({self.limit / (1024 * 1024)} MB)."


@dataclass(slots=True)
class ImageIsEmptyError(BaseAppError):
    @property
    def message(self) -> str:
        return "Image is empty."


@dataclass(slots=True)
class ImageNotFoundError(BaseAppError):
    image_id: ImageId

    @property
    def message(self) -> str:
        return f"Image (id={self.image_id.value}) not found."


@dataclass(slots=True)
class ImageAlreadyHasOwnerError(BaseAppError):
    image_id: ImageId

    @property
    def message(self) -> str:
        return f"Image (id={self.image_id.value}) has another owner."


@dataclass(slots=True)
class ImageConversionError(BaseAppError):
    path: Path
    reason: str

    @property
    def message(self) -> str:
        return f"Image (name=`{self.path.name}`) could not be converted. Reason: `{self.reason}`."
