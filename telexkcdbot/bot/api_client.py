from datetime import date, datetime

import aiohttp
from loguru import logger

from telexkcdbot.models import ComicData, ComicHeadlineInfo, TotalComicData


class APIClient:
    session: aiohttp.ClientSession

    async def create(self) -> None:
        # TODO: raise_for_status
        self.session = aiohttp.ClientSession(base_url="http://localhost:8080")

    async def check_connection(self):
        async with self.session.get("/api") as resp:
            status = (await resp.json())["status"]

            if status == "OK":
                logger.info("API is available")

    async def add_new_comic(self, comic_data: TotalComicData):
        async with self.session.post(
            "/api/comics",
            json={
                "comic_id": comic_data.comic_id,
                "title": comic_data.title,
                "img_url": comic_data.img_url,
                "comment": comic_data.comment,
                "public_date": str(comic_data.public_date),
            },
        ) as resp:
            print(resp)

    async def get_latest_comic_id(self):
        # /api/comics/latest/?field=comic_id
        async with self.session.get("/api/comics/latest_id") as resp:
            latest_id = (await resp.json())["latest_id"]
            return latest_id

    async def get_all_comics_ids(self):
        # /api/comics/?field=comic_id
        async with self.session.get("/api/comics/comics_ids") as resp:
            comics_ids = (await resp.json())["comic_ids"]
            return comics_ids

    async def get_all_ru_comics_ids(self):
        # /api/comics/?field=comic_id&lang={lang}
        async with self.session.get("/api/comics/ru_comics_ids") as resp:
            comics_ids = (await resp.json())["ru_comic_ids"]
            return comics_ids

    async def get_comic_data_by_id(self, comic_id: int):
        # /api/comics/{comic_id}
        async with self.session.get(f"/api/comics/{comic_id}") as resp:
            comic_data = await resp.json()
            comic_data["public_date"] = datetime.strptime(comic_data["public_date"], "%Y-%m-%d").date()
            return ComicData(**comic_data)

    async def get_comics_headlines_by_title(self, title: str, lang: str):
        # /api/comics/search?fields=comic_id,title,img_url&lang={lang}
        async with self.session.get(f"/api/comics/headlines/?title={title}&{lang}=lang") as resp:
            headline_info = await resp.json()
            headline_info = [ComicHeadlineInfo(**x) for x in headline_info]
            return headline_info

    async def get_comics_headlines_by_ids(self, ids: list[int], lang: str):
        # /api/comics/search?fields=comic_id,title,img_url&ids=1,2,3&lang={lang}
        # TODO: remove, use MtM for bookmarks ids
        async with self.session.get(f"/api/comics/headlines/?ids={ids}&{lang}=lang") as resp:
            headline_info = await resp.json()
            headline_info = [ComicHeadlineInfo(**x) for x in headline_info]
            return headline_info

    async def toggle_spec_status(self, comic_id: int):
        # /api/comics/{comic_id} data = ...
        async with self.session.patch(f"/api/comics/spec_status/?comic_id={comic_id}") as resp:
            print(resp)

    async def add_user(self, user_id: int):
        async with self.session.post("/api/users", json={"user_id": user_id}) as resp:
            print(resp)

    async def delete_user(self, user_id: int):
        async with self.session.delete(f"/api/users/{user_id}") as resp:
            print(resp)

    async def get_user_lang(self, user_id: int):
        async with self.session.get(f"/api/users/{user_id}/user_lang") as resp:
            print(resp)

    async def set_user_lang(self, user_id: int, lang: str):
        async with self.session.patch(f"/api/users/{user_id}", data={"user_lang": lang}) as resp:
            print(resp)

    async def get_last_comic_info(self, user_id: int):
        async with self.session.get(f"/api/users/{user_id}/last_comic_info") as resp:
            print(resp)

    async def get_all_users_ids(self):
        async with self.session.get("/api/users/user_ids") as resp:
            print(resp)

    async def get_only_ru_mode_status(self, user_id: int):
        async with self.session.get(f"/api/users/only_ru_mode_status?user={user_id}") as resp:
            print(resp)

    async def get_ban_status(self, user_id: int):
        async with self.session.get(f"/api/users/ban_status?user={user_id}") as resp:
            print(resp)

    async def ban_user(self, user_id: int):
        async with self.session.patch(f"/api/users/{user_id}", data={"is_banned": True}) as resp:
            print(resp)

    async def get_lang_btn_status(self, user_id: int):
        async with self.session.get(f"/api/users/lang_btn_status?user={user_id}") as resp:
            print(resp)

    async def toggle_lang_btn_status(self, user_id: int):
        async with self.session.patch(f"/api/comics/lang_btn_status?user={user_id}") as resp:
            print(resp)

    async def toggle_only_ru_mode_status(self, user_id: int):
        async with self.session.patch(f"/api/comics/only_ru_mode_status/{user_id}") as resp:
            print(resp)

    async def update_last_comic_info(self, user_id: int, new_comic_id: int, new_comic_lang: str):
        async with self.session.patch(
            f"/api/comics/last_comic_info/{user_id}",
            data={"new_comic_id": new_comic_id, "new_comic_lang": new_comic_lang},
        ) as resp:
            print(resp)

    async def update_last_action_date(self, user_id: int, action_date: date):
        async with self.session.patch(
            f"/api/comics/last_action_date/{user_id}", data={"action_date": action_date}
        ) as resp:
            print(resp)

    async def get_admin_users_info(self):
        async with self.session.get("/api/users/admin_users_info") as resp:
            print(resp)

    async def get_user_menu_info(self):
        async with self.session.get("/api/users/user_menu_info") as resp:
            print(resp)

    async def get_bookmarks(self, user_id: int):
        async with self.session.get(f"/api/users/bookmarks?user={user_id}") as resp:
            print(resp)

    async def update_bookmarks(self, user_id: int, new_bookmarks: list[int]):
        async with self.session.patch(
            f"/api/users/bookmarks?user={user_id}", data={"new_bookmarks": new_bookmarks}
        ) as resp:
            print(resp)

    async def get_notification_sound_status(self, user_id: int):
        async with self.session.get(f"/api/users/notification_sound_status?user={user_id}") as resp:
            print(resp)

    async def toggle_notification_sound_status(self, user_id: int):
        async with self.session.patch(f"/api/users/notification_sound_status?user={user_id}") as resp:
            print(resp)


api = APIClient()
