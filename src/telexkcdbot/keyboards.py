from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from src.telexkcdbot.databases.users_db import users_db
from src.telexkcdbot.config import ADMIN_ID
from src.telexkcdbot.models import ComicData


class Keyboard:
    btns_dict: dict = {
        'nav_first': InlineKeyboardButton(text='|<<', callback_data='nav_first'),
        'nav_prev': InlineKeyboardButton(text='<Prev', callback_data='nav_prev'),
        'nav_random': InlineKeyboardButton(text='Rand', callback_data='nav_random'),
        'nav_next': InlineKeyboardButton(text='Next>', callback_data='nav_next'),
        'nav_last': InlineKeyboardButton(text='>>|', callback_data='nav_last'),
        'not_bookmarked': InlineKeyboardButton(text='❤Bookmark', callback_data='bookmark'),
        'bookmarked': InlineKeyboardButton(text='💔Unbookmark', callback_data='unbookmark'),
        'explain': InlineKeyboardButton(text='Explain', callback_data='explain'),
        'ru': InlineKeyboardButton(text='🇷🇺RU', callback_data='ru'),
        'en': InlineKeyboardButton(text='🇬🇧EN', callback_data='en'),

        'flip_break': InlineKeyboardButton(text='Break', callback_data='flip_break'),
        'flip_next': InlineKeyboardButton(text='Next>', callback_data='flip_next'),
        'flip_not_bookmarked': InlineKeyboardButton(text='❤Bookmark', callback_data='flip_bookmark'),
        'flip_bookmarked': InlineKeyboardButton(text='💔Unbookmark', callback_data='flip_unbookmark'),
        'flip_explain': InlineKeyboardButton(text='Explain', callback_data='flip_explain'),
        'flip_ru': InlineKeyboardButton(text='🇷🇺RU', callback_data='flip_ru'),
        'flip_en': InlineKeyboardButton(text='🇬🇧EN', callback_data='flip_en'),

        'notification_sound_on': InlineKeyboardButton(text='🔔 Enable notification sound',
                                                      callback_data='notification_sound_on'),
        'notification_sound_off': InlineKeyboardButton(text='🔕 Disable notification sound',
                                                       callback_data='notification_sound_off'),
        'only_ru_mode_on': InlineKeyboardButton(text='Только переводы вкл.', callback_data='only_ru_mode_on'),
        'only_ru_mode_off': InlineKeyboardButton(text='Только переводы выкл.', callback_data='only_ru_mode_off'),
        'user_bookmarks': InlineKeyboardButton(text='🔖My Bookmarks', callback_data='user_bookmarks'),
        'add_lang_btn': InlineKeyboardButton(text='Add 🇷🇺LANG🇬🇧 Button', callback_data='add_lang_btn'),
        'remove_lang_btn': InlineKeyboardButton(text='Remove 🇷🇺LANG🇬🇧 Button', callback_data='remove_lang_btn'),
        'start_xkcding': InlineKeyboardButton(text='Start xkcding!', callback_data='start_xkcding'),
        'continue_xkcding': InlineKeyboardButton(text='Continue xkcding!', callback_data='continue_xkcding'),
        'menu': InlineKeyboardButton(text='Menu', callback_data='menu'),

        'users_info': InlineKeyboardButton(text='USERS\' INFO', callback_data='users_info'),
        'change_spec_status': InlineKeyboardButton(text='CHANGE SPEC STATUS', callback_data='change_spec_status'),
        'send_actions': InlineKeyboardButton(text='SEND ACTLOG', callback_data='send_actions'),
        'send_errors': InlineKeyboardButton(text='SEND ERRLOG', callback_data='send_errors'),
        'broadcast_admin_msg': InlineKeyboardButton(text='BROADCAST', callback_data='broadcast_admin_msg')
    }

    async def _create_keyboard(self, btns_keys: list[str], row_width: int) -> InlineKeyboardMarkup:
        btns = [self.btns_dict[key] for key in btns_keys]

        keyboard = InlineKeyboardMarkup(row_width=row_width)
        keyboard.add(*btns)
        return keyboard

    @staticmethod
    async def _lang_btn_insertion(user_id: int,
                                  row: list[str],
                                  has_ru: bool,
                                  cur_comic_lang: str,
                                  kb: str) -> list[str]:

        lang_btn_enabled = await users_db.get_lang_btn_status(user_id)
        if lang_btn_enabled and has_ru:
            if cur_comic_lang == 'en':
                lang_btn_key = 'ru' if kb == 'nav' else 'flip_ru'
            else:
                lang_btn_key = 'en' if kb == 'nav' else 'flip_en'
            row.insert(1, lang_btn_key)
        return row

    async def menu(self, user_id: int) -> InlineKeyboardMarkup:
        last_comic_id, _ = await users_db.get_last_comic_info(user_id)
        lang_btn_enabled = await users_db.get_lang_btn_status(user_id)
        notification_sound = await users_db.get_notification_sound_status(user_id)
        only_ru_mode = await users_db.get_only_ru_mode_status(user_id)

        lang_action_btn_key = 'remove_lang_btn' if lang_btn_enabled else 'add_lang_btn'
        notification_sound_btn_key = 'notification_sound_off' if notification_sound else 'notification_sound_on'
        xkcding_btn_key = 'start_xkcding' if last_comic_id == 0 else 'continue_xkcding'
        only_ru_mode_btn_key = 'only_ru_mode_off' if only_ru_mode else 'only_ru_mode_on'

        btns_keys = [notification_sound_btn_key, only_ru_mode_btn_key, 'user_bookmarks',
                     lang_action_btn_key, xkcding_btn_key]
        return await self._create_keyboard(btns_keys, row_width=1)

    async def navigation(self, user_id: int, comic_data: ComicData, comic_lang: str = 'en') -> InlineKeyboardMarkup:
        user_bookmarks = await users_db.get_bookmarks(user_id)

        bookmark_btn = 'bookmarked' if comic_data.comic_id in user_bookmarks else 'not_bookmarked'
        first_row_btns_keys = ['explain', bookmark_btn]
        first_row_btns_keys = await self._lang_btn_insertion(user_id,
                                                             first_row_btns_keys,
                                                             comic_data.has_ru_translation,
                                                             comic_lang,
                                                             kb='nav')
        second_row_btns_keys = ['nav_first', 'nav_prev', 'nav_random', 'nav_next', 'nav_last']

        keyboard = InlineKeyboardMarkup()
        keyboard.row(*[self.btns_dict[key] for key in first_row_btns_keys])
        keyboard.row(*[self.btns_dict[key] for key in second_row_btns_keys])
        return keyboard

    async def flipping(self, user_id: int, comic_data: ComicData, cur_comic_lang: str) -> InlineKeyboardMarkup:
        user_bookmarks = await users_db.get_bookmarks(user_id)

        bookmark_btn_key = 'flip_bookmarked' if comic_data.comic_id in user_bookmarks else 'flip_not_bookmarked'
        btns_keys = ['flip_explain', bookmark_btn_key, 'flip_break', 'flip_next']
        btns_keys = await self._lang_btn_insertion(user_id,
                                                   btns_keys,
                                                   comic_data.has_ru_translation,
                                                   cur_comic_lang,
                                                   kb='flip')

        row_width = 2 if len(btns_keys) == 4 else 3
        return await self._create_keyboard(btns_keys, row_width=row_width)

    async def menu_or_xkcding(self, user_id: int) -> InlineKeyboardMarkup:
        last_comic_id, _ = await users_db.get_last_comic_info(user_id)

        xkcding_btn_key = 'start_xkcding' if last_comic_id == 0 else 'continue_xkcding'
        btns_keys = ['menu', xkcding_btn_key]
        return await self._create_keyboard(btns_keys, row_width=2)

    async def admin_panel(self) -> InlineKeyboardMarkup:
        last_comic_id, _ = await users_db.get_last_comic_info(ADMIN_ID)
        xkcding_btn_key = 'start_xkcding' if last_comic_id == 0 else 'continue_xkcding'

        btns_keys = ['users_info', 'change_spec_status', 'send_actions',
                     'send_errors', 'broadcast_admin_msg', xkcding_btn_key]
        return await self._create_keyboard(btns_keys, row_width=1)


kboard = Keyboard()
