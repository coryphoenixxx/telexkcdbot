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
        'empty_bookmark': InlineKeyboardButton(text='Bookmark\u2606', callback_data='bookmark'),
        'glow_bookmark': InlineKeyboardButton(text='Bookmark🌟', callback_data='bookmark'),
        'explain': InlineKeyboardButton(text='Explain', callback_data='explain'),
        'rus': InlineKeyboardButton(text='Rus', callback_data='rus'),

        'stop': InlineKeyboardButton(text='Stop', callback_data='stop'),
        'go_next': InlineKeyboardButton(text='Next>', callback_data='go_next'),
        'rl_empty_bookmark': InlineKeyboardButton(text='Bookmark\u2606', callback_data='rl_bookmark'),
        'rl_glow_bookmark': InlineKeyboardButton(text='Bookmark🌟', callback_data='rl_bookmark'),
        'rl_explain': InlineKeyboardButton(text='Explain', callback_data='rl_explain'),
        'rl_rus': InlineKeyboardButton(text='Rus', callback_data='rl_rus'),

        'subscribe': InlineKeyboardButton(text='Subscribe🔔', callback_data='subscribe'),
        'unsubscribe': InlineKeyboardButton(text='Unsubscribe🔕', callback_data='unsubscribe'),
        'bookmarks': InlineKeyboardButton(text='My Bookmarks🔖', callback_data='bookmarks'),
        'read_xkcd': InlineKeyboardButton(text='Read xkcd!', callback_data='read_xkcd')
    }

    async def _create_keyboard(self, button_names, row_width):
        buttons = [self.buttons_dict[key] for key in button_names]
        keyboard = InlineKeyboardMarkup(row_width=row_width, one_time_keyboard=True)
        keyboard.add(*buttons)
        return keyboard

    async def navigation(self, user_id, comic_id):
        bookmark_btn_type = 'glow_bookmark' if comic_id in await users_db.bookmarks(user_id) else 'empty_bookmark'
        buttons_names = ['nav_first', 'nav_prev', 'nav_random', 'nav_next', 'nav_last', 'explain', bookmark_btn_type]
        if comic_id in parser.real_rus_ids:
            buttons_names.append('rus')

        return await self._create_keyboard(buttons_names, row_width=5)

    async def stop_next(self, user_id, comic_id):
        bookmark_btn_type = 'rl_glow_bookmark' if comic_id in await users_db.bookmarks(user_id) else 'rl_empty_bookmark'
        buttons_names = [bookmark_btn_type, 'rl_explain', 'stop', 'go_next']
        if comic_id in parser.real_rus_ids:
            buttons_names.insert(2, 'rl_rus')

        return await self._create_keyboard(buttons_names, row_width=3)

    async def menu(self, user_id):
        sub_btn_type = 'unsubscribe' if user_id in (await users_db.subscribed_users) else 'subscribe'
        buttons_names = [sub_btn_type, 'bookmarks', 'read_xkcd']

        return await self._create_keyboard(buttons_names, row_width=2)


kb = Keyboard()
