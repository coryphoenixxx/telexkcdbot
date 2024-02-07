from pathlib import Path

from pydantic import BaseModel


class ImageProcessInMessage(BaseModel):
    image_id: int
    original_abs_path: Path


class ImageProcessOutMessage(BaseModel):
    image_id: int
    converted_abs_path: Path | None
    thumbnail_abs_path: Path
