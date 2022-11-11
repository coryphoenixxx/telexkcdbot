from typing import Any

from aiogram import types
from aiogram.contrib.middlewares.i18n import I18nMiddleware
from bot.api_client import api
from bot.config import I18N_DOMAIN, LOCALES_DIR


class Localization(I18nMiddleware):
    async def get_user_locale(self, action: str, args: tuple[Any]) -> str:
        user = types.User.get_current()
        return await api.get_user_lang(user.id)

    async def set_user_locale(self, locale: str) -> None:
        """Forcibly set the locale to the context"""

        self.ctx_locale.set(locale)


localization = Localization(domain=I18N_DOMAIN, path=LOCALES_DIR)

_ = localization.lazy_gettext
