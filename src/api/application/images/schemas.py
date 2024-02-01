from pydantic import BaseModel


class TranslationImageResponseSchema(BaseModel):
    id: int
    original_rel_path: str
    converted_rel_path: str
    thumbnail_rel_path: str
