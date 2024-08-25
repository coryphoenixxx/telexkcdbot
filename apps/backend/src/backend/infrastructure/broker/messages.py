from pydantic import BaseModel


class ImageProcessInMessage(BaseModel):
    image_id: int
