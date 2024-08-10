from pathlib import Path

from api.core.value_objects import TranslationImageID
from pydantic import BaseModel


class ImageProcessInMessage(BaseModel):
    image_id: TranslationImageID


class ImageProcessOutMessage(BaseModel):
    image_id: TranslationImageID
    converted_abs_path: Path | None
    thumbnail_abs_path: Path
