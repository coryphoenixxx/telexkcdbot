from dataclasses import dataclass
from datetime import date


@dataclass
class ComicHeadlineInfo:
    comic_id: int
    title: str
    img_url: str


@dataclass
class ComicData:
    """Common comic data"""
    comic_id: int
    title: str
    img_url: str
    comment: str
    public_date: date
    is_specific: bool
    has_ru_translation: bool


@dataclass
class XKCDComicData:
    comic_id: int = 404
    title: str = '404'
    img_url: str = 'https://www.explainxkcd.com/wiki/images/9/92/not_found.png'
    comment: str = 'Page not found!'
    public_date: date = date(day=1, month=4, year=2008)
    is_specific: bool = False


@dataclass
class RuComicData:
    ru_title: str = ''
    ru_img_url: str = ''
    ru_comment: str = ''
    has_ru_translation: bool = False


@dataclass
class TotalComicData(RuComicData, XKCDComicData):
    """
    Multiple inheritance sucks!
    Put classes in that order for saving order of their default values.
    So weird.
    """
    pass


@dataclass
class UserMenuInfo:
    notification_sound_status: bool
    only_ru_mode_status: bool
    lang_btn_status: bool
    last_comic_id: int
