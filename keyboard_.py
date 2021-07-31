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
        'rus': InlineKeyboardButton(text='Rus', callback_data='rus'),

        'iter_stop': InlineKeyboardButton(text='Stop', callback_data='iter_stop'),
        'iter_step': InlineKeyboardButton(text='Next>', callback_data='iter_step'),
        'iter_not_bookmarked': InlineKeyboardButton(text='❤Bookmark', callback_data='iter_bookmark'),
        'iter_bookmarked': InlineKeyboardButton(text='💔Unbookmark', callback_data='iter_bookmark'),
        'iter_explain': InlineKeyboardButton(text='Explain', callback_data='iter_explain'),
        'iter_rus': InlineKeyboardButton(text='Rus', callback_data='iter_rus'),

        'subscribe': InlineKeyboardButton(text='🔔Subscribe', callback_data='subscribe'),
        'unsubscribe': InlineKeyboardButton(text='🔕Unsubscribe', callback_data='unsubscribe'),
        'user_bookmarks': InlineKeyboardButton(text='🔖My Bookmarks', callback_data='user_bookmarks'),
        'read_xkcd': InlineKeyboardButton(text='Read xkcd!', callback_data='read_xkcd')
    }

    async def _create_keyboard(self, button_names, row_width):
        buttons = [self.buttons_dict[key] for key in button_names]
        keyboard = InlineKeyboardMarkup(row_width=row_width)
        keyboard.add(*buttons)
        return keyboard

    async def navigation(self, user_id, comic_id):
        bookmark_btn_type = 'bookmarked' if comic_id in await users_db.bookmarks(user_id) else 'not_bookmarked'
        buttons_names = ['nav_first', 'nav_prev', 'nav_random', 'nav_next', 'nav_last', 'explain', bookmark_btn_type]
        if comic_id in parser.real_rus_ids:
            buttons_names.append('rus')

        return await self._create_keyboard(buttons_names, row_width=5)

    async def iteration(self, user_id, comic_id):
        bookmark_btn_type = 'iter_bookmarked' if comic_id in await users_db.bookmarks(user_id) else 'iter_not_bookmarked'
        buttons_names = [bookmark_btn_type, 'iter_explain', 'iter_stop', 'iter_step']
        if comic_id in parser.real_rus_ids:
            buttons_names.insert(2, 'iter_rus')

        row_width = 2 if len(buttons_names) == 4 else 3
        return await self._create_keyboard(buttons_names, row_width=row_width)

    async def menu(self, user_id):
        sub_btn_type = 'unsubscribe' if user_id in (await users_db.subscribed_users) else 'subscribe'
        buttons_names = [sub_btn_type, 'user_bookmarks', 'read_xkcd']

        return await self._create_keyboard(buttons_names, row_width=2)


kboard = Keyboard()


if __name__ == '__main__':
    pass
