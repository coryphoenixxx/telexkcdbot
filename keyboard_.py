from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from loader import users_db
from parser_ import parser


class Keyboard:
    buttons_dict = {
        'nav_first': InlineKeyboardButton(text='|<<', callback_data='nav_first'),
        'nav_prev': InlineKeyboardButton(text='<Prev', callback_data='nav_prev'),
        'nav_random': InlineKeyboardButton(text='Rand', callback_data='nav_random'),
        'nav_next': InlineKeyboardButton(text='Next>', callback_data='nav_next'),
        'nav_last': InlineKeyboardButton(text='>>|', callback_data='nav_last'),
        'not_bookmarked': InlineKeyboardButton(text='❤Bookmark', callback_data='bookmark'),
        'bookmarked': InlineKeyboardButton(text='💔Unbookmark', callback_data='bookmark'),
        'explain': InlineKeyboardButton(text='Explain', callback_data='explain'),
        'ru': InlineKeyboardButton(text='RU', callback_data='ru'),

        'trav_stop': InlineKeyboardButton(text='Stop', callback_data='trav_stop'),
        'trav_step': InlineKeyboardButton(text='Next>', callback_data='trav_step'),
        'trav_not_bookmarked': InlineKeyboardButton(text='❤Bookmark', callback_data='trav_bookmark'),
        'trav_bookmarked': InlineKeyboardButton(text='💔Unbookmark', callback_data='trav_bookmark'),
        'trav_explain': InlineKeyboardButton(text='Explain', callback_data='trav_explain'),
        'trav_ru': InlineKeyboardButton(text='RU', callback_data='trav_ru'),

        'subscribe': InlineKeyboardButton(text='🔔Subscribe', callback_data='subscribe'),
        'unsubscribe': InlineKeyboardButton(text='🔕Unsubscribe', callback_data='unsubscribe'),
        'user_bookmarks': InlineKeyboardButton(text='🔖My Bookmarks', callback_data='user_bookmarks'),
        'remove_ru': InlineKeyboardButton(text='Remove 🇷🇺RU button', callback_data='remove_ru'),
        'add_ru': InlineKeyboardButton(text='Add 🇷🇺RU Button', callback_data='add_ru'),
        'read_xkcd': InlineKeyboardButton(text='Read xkcd!', callback_data='read_xkcd')
    }

    async def _create_keyboard(self, button_names, row_width):
        buttons = [self.buttons_dict[key] for key in button_names]
        keyboard = InlineKeyboardMarkup(row_width=row_width)
        keyboard.add(*buttons)
        return keyboard

    async def menu(self, user_id):
        ru_btn = 'remove_ru' if (await users_db.get_user_lang(user_id)) == 'ru' else 'add_ru'
        sub_btn = 'unsubscribe' if user_id in (await users_db.subscribed_users) else 'subscribe'
        buttons_names = [sub_btn, 'user_bookmarks', ru_btn, 'read_xkcd']

        return await self._create_keyboard(buttons_names, row_width=1)

    async def navigation(self, user_id, comic_id):
        bookmark_btn_type = 'bookmarked' if comic_id in await users_db.get_bookmarks(user_id) else 'not_bookmarked'
        buttons_names = ['nav_first', 'nav_prev', 'nav_random', 'nav_next', 'nav_last', 'explain', bookmark_btn_type]

        # add RU button
        if (await users_db.get_user_lang(user_id)) == 'ru':
            if comic_id in parser.real_ru_ids:
                buttons_names.append('ru')

        return await self._create_keyboard(buttons_names, row_width=5)

    async def traversal(self, user_id, comic_id):
        bookmark_btn_type = 'trav_bookmarked' if comic_id in await users_db.get_bookmarks(user_id) \
                                              else 'trav_not_bookmarked'
        buttons_names = [bookmark_btn_type, 'trav_explain', 'trav_stop', 'trav_step']

        # add RU button
        if (await users_db.get_user_lang(user_id)) == 'ru':
            if comic_id in parser.real_ru_ids:
                buttons_names.insert(2, 'trav_ru')

        row_width = 2 if len(buttons_names) == 4 else 3

        return await self._create_keyboard(buttons_names, row_width=row_width)


kboard = Keyboard()

if __name__ == '__main__':
    pass
