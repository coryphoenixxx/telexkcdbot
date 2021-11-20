from typing import Any, Tuple, Optional

from aiogram import types, Dispatcher
from aiogram.contrib.middlewares.i18n import I18nMiddleware

from src.telexkcdbot.databases.users_db import users_db
from src.telexkcdbot.config import I18N_DOMAIN, LOCALES_DIR


class ACLMiddleware(I18nMiddleware):
    async def get_user_locale(self, action: str, args: tuple[Any]) -> str:
        user = types.User.get_current()
        lang = await users_db.get_user_lang(user.id)
        return lang

    async def set_user_locale(self, locale: str):
        self.ctx_locale.set(locale)


i18n = ACLMiddleware(I18N_DOMAIN, LOCALES_DIR)

_ = i18n.lazy_gettext
