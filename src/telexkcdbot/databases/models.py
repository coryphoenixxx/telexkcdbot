from dataclasses import dataclass
from datetime import date


@dataclass
class ComicHeadlineInfo:
    comic_id: int
    title: str
    img_url: str


@dataclass
class ComicData:
    comic_id: int
    title: str
    img_url: str
    comment: str
    public_date: date
    is_specific: bool
    has_ru_translation: bool
