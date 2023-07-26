import functools
from dataclasses import asdict, dataclass, fields


@dataclass
class Comic:
    comic_id: int
    title: str
    image: str
    comment: str
    transcript: str
    publication_date: str
    favorite_count: int
    is_specific: bool
    rus_title: str
    rus_image: str
    rus_comment: str
    rus_transcript: str

    def filter_fields(self, fields_: str | None) -> dict:
        if fields_:
            return {k: v for (k, v) in asdict(self).items() if k in fields_.split(',')}
        return asdict(self)

    @classmethod
    @property
    @functools.cache
    def field_names(cls) -> tuple:
        return tuple(field.name for field in fields(cls))
