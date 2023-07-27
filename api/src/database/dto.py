import functools
from dataclasses import asdict, dataclass, fields


@dataclass
class ComicTranslation:
    language_code: str
    title: str
    image_url: str
    comment: str
    transcript: str

    def as_dict(self):
        return {
            self.language_code: {
                'title': self.title,
                'image_url': self.image_url,
                'comment': self.comment,
                'transcript': self.transcript,
            },
        }


@dataclass
class ComicFlatten:
    comic_id: int
    favorite_count: int
    is_specific: bool
    publication_date: str
    title: str
    image_url: str
    comment: str
    transcript: str

    @classmethod
    @property
    @functools.cache
    def field_names(cls) -> tuple:
        return tuple(field.name for field in fields(cls))


@dataclass
class Comic:
    comic_id: int
    favorite_count: int
    is_specific: bool
    publication_date: str
    translations: dict

    def flatten(self, fields_, language: str):
        base_data = self.filter_fields(fields_)
        translation_data = base_data.pop('translations').get(language)
        return base_data | translation_data

    def filter_fields(self, fields_: str | None) -> dict:
        if fields_:
            fields_ = fields_.split(',')
            comic_dict = {k: v for (k, v) in asdict(self).items() if k in fields_}

            comic_dict_tr = {}
            for lang_code, d in self.translations.items():
                comic_dict_tr[lang_code] = {}
                for k, v in d.items():
                    if k in fields_:
                        comic_dict_tr[lang_code][k] = v

            comic_dict['translations'] = comic_dict_tr

            return comic_dict
        return asdict(self)
