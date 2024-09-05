from pydantic import BaseModel


class ConvertImageMessage(BaseModel):
    image_id: int


class NewComicMessage(BaseModel):
    comic_id: int
