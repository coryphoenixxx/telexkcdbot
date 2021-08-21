from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.loader import *
from bot.config import ADMIN_ID


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

        'trav_stop': InlineKeyboardButton(text='Stop', callback_data='trav_stop'),
        'trav_step': InlineKeyboardButton(text='Next>', callback_data='trav_step'),
        'trav_not_bookmarked': InlineKeyboardButton(text='❤Bookmark', callback_data='trav_bookmark'),
        'trav_bookmarked': InlineKeyboardButton(text='💔Unbookmark', callback_data='trav_unbookmark'),
        'trav_explain': InlineKeyboardButton(text='Explain', callback_data='trav_explain'),
        'trav_ru': InlineKeyboardButton(text='🇷🇺RU', callback_data='trav_ru'),
        'trav_en': InlineKeyboardButton(text='🇬🇧EN', callback_data='trav_en'),

        'subscribe': InlineKeyboardButton(text='🔔Subscribe', callback_data='subscribe'),
        'unsubscribe': InlineKeyboardButton(text='🔕Unsubscribe', callback_data='unsubscribe'),
        'user_bookmarks': InlineKeyboardButton(text='🔖My Bookmarks', callback_data='user_bookmarks'),
        'add_lang_btn': InlineKeyboardButton(text='Add 🇷🇺LANG🇬🇧 Button', callback_data='add_lang_btn'),
        'remove_lang_btn': InlineKeyboardButton(text='Remove 🇷🇺LANG🇬🇧 Button', callback_data='remove_lang_btn'),
        'start_xkcding': InlineKeyboardButton(text='Start xkcding!', callback_data='start_xkcding'),
        'continue_xkcding': InlineKeyboardButton(text='Continue xkcding!', callback_data='continue_xkcding'),
        'menu': InlineKeyboardButton(text='Menu', callback_data='menu'),

        'change_spec_status': InlineKeyboardButton(text='CHANGE SPEC STATUS', callback_data='change_spec_status'),
        'send_actions': InlineKeyboardButton(text='SEND ACTLOG', callback_data='send_actions'),
        'send_errors': InlineKeyboardButton(text='SEND ERRLOG', callback_data='send_errors'),
        'users_info': InlineKeyboardButton(text='USERS\' INFO', callback_data='users_info'),
        'broadcast': InlineKeyboardButton(text='BROADCAST', callback_data='broadcast')
    }

    async def _create_keyboard(self, btns_keys: list, row_width: int) -> InlineKeyboardMarkup:
        btns = [self.btns_dict[key] for key in btns_keys]
        keyboard = InlineKeyboardMarkup(row_width=row_width)
        keyboard.add(*btns)

        return keyboard

    @staticmethod
    async def _lang_btn_insertion(row: list, user_id: int, comic_id: int, comic_lang: str) -> list:
        user_lang = await users_db.get_user_lang(user_id)

        if user_lang == 'ru':
            if comic_id in parser.real_ru_comics_ids:
                if comic_lang == 'en':
                    row.insert(1, 'ru')
                else:
                    row.insert(1, 'en')

        return row

    async def menu(self, user_id: int) -> InlineKeyboardMarkup:
        comic_id, _ = await users_db.get_cur_comic_info(user_id)
        user_lang = await users_db.get_user_lang(user_id)
        subs = await users_db.get_subscribed_users()

        lang_btn_key = 'remove_lang_btn' if user_lang == 'ru' else 'add_lang_btn'
        sub_btn_key = 'unsubscribe' if user_id in subs else 'subscribe'
        xkcding_btn_key = 'start_xkcding' if comic_id == 0 else 'continue_xkcding'
        btns_keys = [sub_btn_key, 'user_bookmarks', lang_btn_key, xkcding_btn_key]

        return await self._create_keyboard(btns_keys, row_width=1)

    async def navigation(self, user_id: int, comic_id: int, comic_lang: str = 'en') -> InlineKeyboardMarkup:
        user_bookmarks = await users_db.get_bookmarks(user_id)

        bookmark_btn = 'bookmarked' if comic_id in user_bookmarks else 'not_bookmarked'
        first_row_btns_keys = ['explain', bookmark_btn]
        first_row_btns_keys = await self._lang_btn_insertion(first_row_btns_keys, user_id, comic_id, comic_lang)
        second_row_btns_keys = ['nav_first', 'nav_prev', 'nav_random', 'nav_next', 'nav_last']

        keyboard = InlineKeyboardMarkup()

        keyboard.row(*[self.btns_dict[key] for key in first_row_btns_keys])
        keyboard.row(*[self.btns_dict[key] for key in second_row_btns_keys])

        return keyboard

    async def traversal(self, user_id: int, comic_id: int, comic_lang: str) -> InlineKeyboardMarkup:
        user_bookmarks = await users_db.get_bookmarks(user_id)

        bookmark_btn_key = 'trav_bookmarked' if comic_id in user_bookmarks else 'trav_not_bookmarked'
        btns_keys = [bookmark_btn_key, 'trav_explain', 'trav_stop', 'trav_step']
        btns_keys = await self._lang_btn_insertion(btns_keys, user_id, comic_id, comic_lang)

        row_width = 2 if len(btns_keys) == 4 else 3

        return await self._create_keyboard(btns_keys, row_width=row_width)

    async def menu_or_xkcding(self, user_id: int) -> InlineKeyboardMarkup:
        comic_id, _ = await users_db.get_cur_comic_info(user_id)

        xkcding_btn_key = 'start_xkcding' if comic_id == 0 else 'continue_xkcding'
        btns_keys = ['menu', xkcding_btn_key]

        return await self._create_keyboard(btns_keys, row_width=2)

    async def admin_panel(self) -> InlineKeyboardMarkup:
        comic_id, _ = await users_db.get_cur_comic_info(ADMIN_ID)
        xkcding_btn_key = 'start_xkcding' if comic_id == 0 else 'continue_xkcding'

        btns_keys = ['users_info', 'change_spec_status', 'send_actions', 'send_errors', 'broadcast', xkcding_btn_key]

        return await self._create_keyboard(btns_keys, row_width=1)


kboard = Keyboard()

if __name__ == '__main__':
    pass
