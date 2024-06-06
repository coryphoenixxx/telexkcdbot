from pathlib import Path

from api.core.entities import TranslationImageID
from pydantic import BaseModel


class ImageProcessInMessage(BaseModel):
    image_id: TranslationImageID
    original_abs_path: Path


class ImageProcessOutMessage(BaseModel):
    image_id: TranslationImageID
    converted_abs_path: Path | None
    thumbnail_abs_path: Path
