from datetime import date, datetime

from aiohttp import ClientSession
from loguru import logger
from models import (
    AdminUsersInfo,
    ComicData,
    ComicHeadlineInfo,
    MenuKeyboardInfo,
    TotalComicData,
)


class APIClient:
    def __init__(self) -> None:
        self.base_url = f"http://api:8080"

    async def check_connection(self) -> None:
        async with ClientSession(base_url=self.base_url) as session:
            async with session.get("/api") as resp:
                status = (await resp.json())["status"]

                if status == "OK":
                    logger.info("API is available")

    async def add_new_comic(self, comic_data: TotalComicData):
        async with ClientSession(base_url=self.base_url) as session:
            async with session.post(
                "/api/comics",
                json={
                    "comic_id": comic_data.comic_id,
                    "title": comic_data.title,
                    "img_url": comic_data.img_url,
                    "comment": comic_data.comment,
                    "public_date": str(comic_data.public_date),
                    "is_specific": comic_data.is_specific,
                    "ru_title": comic_data.ru_title,
                    "ru_img_url": comic_data.ru_img_url,
                    "ru_comment": comic_data.ru_comment,
                    "has_ru_translation": comic_data.has_ru_translation,
                },
            ) as resp:
                pass

    async def get_latest_comic_id(self):
        # /api/comics/latest/?field=comic_id
        async with ClientSession(base_url=self.base_url) as session:
            async with session.get("/api/comics/latest_id") as resp:
                latest_id = (await resp.json())["latest_id"]
                return latest_id

    async def get_all_comics_ids(self):
        # /api/comics/?field=comic_id
        async with ClientSession(base_url=self.base_url) as session:
            async with session.get("/api/comics/comics_ids") as resp:
                comics_ids = (await resp.json())["comics_ids"]
                return comics_ids

    async def get_all_ru_comics_ids(self):
        # /api/comics/?field=comic_id&lang={lang}
        async with ClientSession(base_url=self.base_url) as session:
            async with session.get("/api/comics/ru_comics_ids") as resp:
                comics_ids = (await resp.json())["ru_comic_ids"]
                return comics_ids

    async def get_comic_data_by_id(self, comic_id: int, comic_lang: str = "en"):
        # /api/comics/{comic_id}
        async with ClientSession(base_url=self.base_url) as session:
            async with session.get(f"/api/comics/?comic_id={comic_id}&comic_lang={comic_lang}") as resp:
                comic_data = await resp.json()
                comic_data["public_date"] = datetime.strptime(comic_data["public_date"], "%Y-%m-%d").date()
                return ComicData(**comic_data)

    async def get_comics_headlines_by_title(self, title: str, lang: str = "en"):
        # /api/comics/search?fields=comic_id,title,img_url&lang={lang}
        async with ClientSession(base_url=self.base_url) as session:
            async with session.get(f"/api/comics/headlines/?title={title}&lang={lang}") as resp:
                headline_info = await resp.json()
                headline_info = [ComicHeadlineInfo(**x) for x in headline_info]
                return headline_info

    async def get_comics_headlines_by_ids(self, ids: list[int], lang: str = "en"):
        # /api/comics/search?fields=comic_id,title,img_url&ids=1,2,3&lang={lang}
        # TODO: remove, use MtM for bookmarks ids
        async with ClientSession(base_url=self.base_url) as session:
            async with session.get(f"/api/comics/headlines/?ids={ids}&lang={lang}") as resp:
                headline_info = await resp.json()
                headline_info = [ComicHeadlineInfo(**x) for x in headline_info]
                return headline_info

    async def toggle_spec_status(self, comic_id: int):
        # /api/comics/{comic_id} data = ...
        async with ClientSession(base_url=self.base_url) as session:
            async with session.patch(f"/api/comics/spec_status/?comic_id={comic_id}") as resp:
                pass

    ###################
    # USER
    ###################

    async def add_user(self, user_id: int):
        async with ClientSession(base_url=self.base_url) as session:
            async with session.post("/api/users", json={"user_id": user_id}) as resp:
                pass

    async def delete_user(self, user_id: int):
        async with ClientSession(base_url=self.base_url) as session:
            async with session.delete(f"/api/users/{user_id}") as resp:
                pass

    async def get_user_lang(self, user_id: int) -> str:
        async with ClientSession(base_url=self.base_url) as session:
            async with session.get(f"/api/users/user_lang/{user_id}") as resp:
                user_lang = (await resp.json())["user_lang"]
                return user_lang

    async def set_user_lang(self, user_id: int, lang: str):
        async with ClientSession(base_url=self.base_url) as session:
            async with session.patch(f"/api/users/user_lang/{user_id}", json={"user_lang": lang}) as resp:
                pass

    async def get_last_comic_info(self, user_id: int):
        async with ClientSession(base_url=self.base_url) as session:
            async with session.get(f"/api/users/last_comic_info/{user_id}") as resp:
                last_comic_info = (await resp.json())["last_comic_info"]
                return last_comic_info

    async def update_last_comic_info(self, user_id: int, new_comic_id: int, new_comic_lang: str):
        async with ClientSession(base_url=self.base_url) as session:
            async with session.patch(
                f"/api/users/last_comic_info/{user_id}",
                json={"new_comic_id": new_comic_id, "new_comic_lang": new_comic_lang},
            ) as resp:
                pass

    async def get_all_users_ids(self):
        async with ClientSession(base_url=self.base_url) as session:
            async with session.get("/api/users/users_ids") as resp:
                users_ids = (await resp.json())["users_ids"]
                return users_ids

    async def get_only_ru_mode_status(self, user_id: int):
        async with ClientSession(base_url=self.base_url) as session:
            async with session.get(f"/api/users/only_ru_mode_status/{user_id}") as resp:
                only_ru_mode_status = (await resp.json())["only_ru_mode_status"]
                return only_ru_mode_status

    async def toggle_only_ru_mode_status(self, user_id: int):
        async with ClientSession(base_url=self.base_url) as session:
            async with session.patch(f"/api/users/only_ru_mode_status/{user_id}") as resp:
                pass

    async def get_ban_status(self, user_id: int):
        async with ClientSession(base_url=self.base_url) as session:
            async with session.get(f"/api/users/ban_status/{user_id}") as resp:
                ban_status = (await resp.json())["ban_status"]
                return ban_status

    async def ban_user(self, user_id: int):
        async with ClientSession(base_url=self.base_url) as session:
            async with session.patch(f"/api/users/{user_id}", json={"is_banned": True}) as resp:
                pass

    async def get_lang_btn_status(self, user_id: int):
        async with ClientSession(base_url=self.base_url) as session:
            async with session.get(f"/api/users/lang_btn_status/{user_id}") as resp:
                lang_btn_status = (await resp.json())["lang_btn_status"]
                return lang_btn_status

    async def toggle_lang_btn_status(self, user_id: int):
        async with ClientSession(base_url=self.base_url) as session:
            async with session.patch(f"/api/users/lang_btn_status/{user_id}") as resp:
                pass

    async def update_last_action_date(self, user_id: int, action_date: date):
        async with ClientSession(base_url=self.base_url) as session:
            async with session.patch(
                f"/api/users/last_action_date/{user_id}", json={"action_date": str(action_date)}
            ) as resp:
                pass

    async def get_user_menu_info(self, user_id: int):
        async with ClientSession(base_url=self.base_url) as session:
            async with session.get(f"/api/users/user_menu_info/{user_id}") as resp:
                user_menu_info = await resp.json()
                return MenuKeyboardInfo(**user_menu_info)

    async def get_bookmarks(self, user_id: int):
        async with ClientSession(base_url=self.base_url) as session:
            async with session.get(f"/api/users/bookmarks/{user_id}") as resp:
                bookmarks = (await resp.json())["bookmarks"]
                return bookmarks

    async def update_bookmarks(self, user_id: int, new_bookmarks: list[int]):
        async with ClientSession(base_url=self.base_url) as session:
            async with session.patch(f"/api/users/bookmarks/{user_id}", json={"new_bookmarks": new_bookmarks}) as resp:
                pass

    async def get_notification_sound_status(self, user_id: int):
        async with ClientSession(base_url=self.base_url) as session:
            async with session.get(f"/api/users/notification_sound_status/{user_id}") as resp:
                notification_sound_status = (await resp.json())["notification_sound_status"]
                return notification_sound_status

    async def toggle_notification_sound_status(self, user_id: int):
        async with ClientSession(base_url=self.base_url) as session:
            async with session.patch(f"/api/users/notification_sound_status/{user_id}") as resp:
                pass

    async def get_admin_users_info(self):
        async with ClientSession(base_url=self.base_url) as session:
            async with session.get("/api/users/admin_users_info") as resp:
                admin_users_info = await resp.json()
                return AdminUsersInfo(**admin_users_info)


api = APIClient()
