from dataclasses import dataclass
from datetime import date


@dataclass
class ComicHeadlineInfo:
    comic_id: int
    title: str
    img_url: str


@dataclass
class ComicData:
    """Used for sending comic to user"""

    comic_id: int
    title: str
    img_url: str
    comment: str
    public_date: date
    is_specific: bool
    has_ru_translation: bool


@dataclass
class XKCDComicData:
    """English-specific comic data"""

    comic_id: int = 404
    title: str = "404"
    img_url: str = "https://www.explainxkcd.com/wiki/images/9/92/not_found.png"
    comment: str = "Page not found!"
    public_date: str = "01-04-2008"
    is_specific: bool = False


@dataclass
class RuComicData:
    ru_title: str = ""
    ru_img_url: str = ""
    ru_comment: str = ""
    has_ru_translation: bool = False


@dataclass
class TotalComicData(RuComicData, XKCDComicData):
    pass


@dataclass
class MenuKeyboardInfo:
    notification_sound_status: bool
    only_ru_mode_status: bool
    lang_btn_status: bool
    user_lang: str
    last_comic_id: int


@dataclass
class AdminUsersInfo:
    users_num: int
    last_week_active_users_num: int
    only_ru_users_num: int
