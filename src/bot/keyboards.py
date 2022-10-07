from dataclasses import astuple

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.callback_data import CallbackData
from src.bot.api_client import api
from src.bot.middlewares.localization import _
from src.config import ADMIN_ID
from src.models import ComicData

support_cb_data = CallbackData("support", "type", "user_id", "message_id")


class Keyboard:
    btns_dict: dict = {
        # Language selection
        "en_user_lang": InlineKeyboardButton(text="🇬🇧English", callback_data="en_user_lang"),
        "ru_user_lang": InlineKeyboardButton(text="🇷🇺Русский", callback_data="ru_user_lang"),
        # Comic
        "nav_first": InlineKeyboardButton(text="|<<", callback_data="nav_first"),
        "nav_prev": InlineKeyboardButton(text=_("<Prev"), callback_data="nav_prev"),
        "nav_random": InlineKeyboardButton(text=_("🎲Rand"), callback_data="nav_random"),
        "nav_next": InlineKeyboardButton(text=_("Next>"), callback_data="nav_next"),
        "nav_last": InlineKeyboardButton(text=">>|", callback_data="nav_last"),
        "not_bookmarked": InlineKeyboardButton(text=_("❤Bookmark"), callback_data="bookmark"),
        "bookmarked": InlineKeyboardButton(text=_("💔Unbookmark"), callback_data="unbookmark"),
        "explain": InlineKeyboardButton(text=_("📜Explain"), callback_data="explain"),
        "ru": InlineKeyboardButton(text="🇷🇺RU", callback_data="ru"),
        "en": InlineKeyboardButton(text="🇬🇧EN", callback_data="en"),
        # Comic in flipping mode
        "flip_break": InlineKeyboardButton(text=_("↩Break"), callback_data="flip_break"),
        "flip_next": InlineKeyboardButton(text=_("Forward>"), callback_data="flip_next"),
        "flip_not_bookmarked": InlineKeyboardButton(text=_("❤Bookmark"), callback_data="flip_bookmark"),
        "flip_bookmarked": InlineKeyboardButton(text=_("💔Unbookmark"), callback_data="flip_unbookmark"),
        "flip_explain": InlineKeyboardButton(text=_("📜Explain"), callback_data="flip_explain"),
        "flip_ru": InlineKeyboardButton(text="🇷🇺RU", callback_data="flip_ru"),
        "flip_en": InlineKeyboardButton(text="🇬🇧EN", callback_data="flip_en"),
        # Menu
        "notification_sound_on": InlineKeyboardButton(
            text=_("🔔 Enable notification sound"),
            callback_data="notification_sound_on",
        ),
        "notification_sound_off": InlineKeyboardButton(
            text=_("🔕 Disable notification sound"),
            callback_data="notification_sound_off",
        ),
        "only_ru_mode_on": InlineKeyboardButton(text="Только переводы вкл.", callback_data="only_ru_mode_on"),
        "only_ru_mode_off": InlineKeyboardButton(text="Только переводы выкл.", callback_data="only_ru_mode_off"),
        "user_bookmarks": InlineKeyboardButton(text=_("📑 My Bookmarks"), callback_data="user_bookmarks"),
        "add_lang_btn": InlineKeyboardButton(text=_("Add 🇷🇺RU/🇬🇧EN Button"), callback_data="add_lang_btn"),
        "admin_support": InlineKeyboardButton(text=_("💬 Admin Support"), callback_data="admin_support"),
        "remove_lang_btn": InlineKeyboardButton(text=_("Remove 🇷🇺RU/🇬🇧EN Button"), callback_data="remove_lang_btn"),
        "start_xkcding": InlineKeyboardButton(text=_("Start xkcding!"), callback_data="start_xkcding"),
        "continue_xkcding": InlineKeyboardButton(text=_("Continue xkcding!"), callback_data="continue_xkcding"),
        "menu": InlineKeyboardButton(text=_("Menu"), callback_data="menu"),
        # Admin
        "users_info": InlineKeyboardButton(text="USERS INFO", callback_data="users_info"),
        "change_spec_status": InlineKeyboardButton(text="CHANGE SPEC STATUS", callback_data="change_spec_status"),
        "send_actions": InlineKeyboardButton(text="SEND ACTLOG", callback_data="send_actions"),
        "send_errors": InlineKeyboardButton(text="SEND ERRLOG", callback_data="send_errors"),
        "broadcast_admin_msg": InlineKeyboardButton(text="BROADCAST", callback_data="broadcast_admin_msg"),
    }

    def _create_keyboard(self, btns_keys: list[str], row_width: int = 2) -> InlineKeyboardMarkup:
        btns = [self.btns_dict[key] for key in btns_keys]

        keyboard = InlineKeyboardMarkup(row_width=row_width)
        keyboard.add(*btns)
        return keyboard

    @staticmethod
    async def _lang_btn_insertion(
        user_id: int,
        row: list[str],
        has_ru: bool,
        cur_comic_lang: str,
        kb: str,
    ) -> list[str]:
        """Inserts 🇷🇺/🇬🇧 button in keyboard under the comic"""

        lang_btn_enabled = await api.get_lang_btn_status(user_id)
        if lang_btn_enabled and has_ru:
            if cur_comic_lang == "en":
                lang_btn_key = "ru" if kb == "nav" else "flip_ru"
            else:
                lang_btn_key = "en" if kb == "nav" else "flip_en"
            row.insert(0, lang_btn_key)
        return row

    async def lang_selection(self) -> InlineKeyboardMarkup:
        btns_keys = ["en_user_lang", "ru_user_lang"]
        return self._create_keyboard(btns_keys)

    async def menu(self, user_id: int) -> InlineKeyboardMarkup:
        user_menu_info = await api.get_user_menu_info(user_id)

        (
            notification_sound,
            only_ru_mode,
            lang_btn_enabled,
            user_lang,
            last_comic_id,
        ) = astuple(user_menu_info)

        notification_sound_btn_key = "notification_sound_off" if notification_sound else "notification_sound_on"
        lang_action_btn_key = "remove_lang_btn" if lang_btn_enabled else "add_lang_btn"
        xkcding_btn_key = "start_xkcding" if last_comic_id == 0 else "continue_xkcding"

        btns_keys = [
            notification_sound_btn_key,
            "user_bookmarks",
            lang_action_btn_key,
            "admin_support",
            xkcding_btn_key,
        ]

        if user_lang == "ru":
            only_ru_mode_btn_key = "only_ru_mode_off" if only_ru_mode else "only_ru_mode_on"
            btns_keys.insert(1, only_ru_mode_btn_key)

        return self._create_keyboard(btns_keys, row_width=1)

    async def navigation(
        self,
        user_id: int,
        comic_data: ComicData,
        comic_lang: str = "en",
        is_explained: bool = False,
    ) -> InlineKeyboardMarkup:

        user_bookmarks = await api.get_bookmarks(user_id)

        bookmark_btn = "bookmarked" if comic_data.comic_id in user_bookmarks else "not_bookmarked"
        first_row_btns_keys = [bookmark_btn]

        first_row_btns_keys = await self._lang_btn_insertion(
            user_id,
            first_row_btns_keys,
            comic_data.has_ru_translation,
            comic_lang,
            kb="nav",
        )

        if not is_explained:
            first_row_btns_keys.insert(0, "explain")

        second_row_btns_keys = [
            "nav_first",
            "nav_prev",
            "nav_random",
            "nav_next",
            "nav_last",
        ]

        keyboard = InlineKeyboardMarkup()
        keyboard.row(*[self.btns_dict[key] for key in first_row_btns_keys])
        keyboard.row(*[self.btns_dict[key] for key in second_row_btns_keys])
        return keyboard

    async def flipping(
        self,
        user_id: int,
        comic_data: ComicData,
        cur_comic_lang: str,
        is_explained: bool = False,
    ) -> InlineKeyboardMarkup:

        user_bookmarks = await api.get_bookmarks(user_id)

        bookmark_btn_key = "flip_bookmarked" if comic_data.comic_id in user_bookmarks else "flip_not_bookmarked"

        btns_keys = [bookmark_btn_key, "flip_break", "flip_next"]
        btns_keys = await self._lang_btn_insertion(
            user_id,
            btns_keys,
            comic_data.has_ru_translation,
            cur_comic_lang,
            kb="flip",
        )

        if not is_explained:
            btns_keys.insert(0, "flip_explain")

        row_width = 2 if len(btns_keys) == 4 else 3

        # Swap "↩Break" and "❤Bookmark"
        if len(btns_keys) == 3:
            btns_keys[0], btns_keys[1] = btns_keys[1], btns_keys[0]

        return self._create_keyboard(btns_keys, row_width=row_width)

    async def menu_or_xkcding(self, user_id: int) -> InlineKeyboardMarkup:
        last_comic_id, _ = await api.get_last_comic_info(user_id)

        xkcding_btn_key = "start_xkcding" if last_comic_id == 0 else "continue_xkcding"
        btns_keys = ["menu", xkcding_btn_key]
        return self._create_keyboard(btns_keys)

    @staticmethod
    async def support_keyboard(user_id: int, message_id: int) -> InlineKeyboardMarkup:
        answer_btn = InlineKeyboardButton(
            text="💬 Answer",
            callback_data=support_cb_data.new(type="answer", user_id=user_id, message_id=message_id),
        )

        ban_btn = InlineKeyboardButton(
            text="🔨 Ban User",
            callback_data=support_cb_data.new(type="ban", user_id=user_id, message_id=message_id),
        )

        keyboard = InlineKeyboardMarkup()
        keyboard.add(answer_btn, ban_btn)

        return keyboard

    async def admin_panel(self) -> InlineKeyboardMarkup:
        last_comic_id, _ = await api.get_last_comic_info(ADMIN_ID)
        xkcding_btn_key = "start_xkcding" if last_comic_id == 0 else "continue_xkcding"

        btns_keys = [
            "users_info",
            "change_spec_status",
            "send_actions",
            "send_errors",
            "broadcast_admin_msg",
            xkcding_btn_key,
        ]
        return self._create_keyboard(btns_keys, row_width=1)


kboard = Keyboard()
