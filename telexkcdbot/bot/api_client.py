from datetime import datetime

import aiohttp
from loguru import logger

from telexkcdbot.models import ComicData, ComicHeadlineInfo, TotalComicData


class ApiClient:
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
        async with self.session.get("/api/comics/latest_id") as resp:
            latest_id = (await resp.json())["latest_id"]
            return latest_id

    async def get_all_comics_ids(self):
        async with self.session.get("/api/comics/comics_ids") as resp:
            comics_ids = (await resp.json())["comic_ids"]
            return comics_ids

    async def get_all_ru_comics_ids(self):
        async with self.session.get("/api/comics/ru_comics_ids") as resp:
            comics_ids = (await resp.json())["ru_comic_ids"]
            return comics_ids

    async def get_comic_data_by_id(self, comic_id: int):
        async with self.session.get(f"/api/comics/{comic_id}") as resp:
            comic_data = await resp.json()
            comic_data["public_date"] = datetime.strptime(comic_data["public_date"], "%Y-%m-%d").date()
            return ComicData(**comic_data)

    async def get_comics_headlines_by_title(self, title: str, lang: str):
        async with self.session.get(f"/api/comics/headlines/?title={title}&{lang}=lang") as resp:
            headline_info = await resp.json()
            headline_info = [ComicHeadlineInfo(**x) for x in headline_info]
            return headline_info

    async def get_comics_headlines_by_ids(self, ids: list[int], lang: str):
        async with self.session.get(f"/api/comics/headlines/?ids={ids}&{lang}=lang") as resp:
            headline_info = await resp.json()
            headline_info = [ComicHeadlineInfo(**x) for x in headline_info]
            return headline_info

    async def toggle_spec_status(self, comic_id: int):
        async with self.session.patch(f"/api/comics/{comic_id}") as resp:
            print(resp)


api = ApiClient()
