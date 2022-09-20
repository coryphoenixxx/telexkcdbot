import aiohttp
from loguru import logger


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

    async def add_new_comic(self):
        async with self.session.post("/api/comics") as resp:
            print(resp)

    async def get_latest_comic_id(self):
        async with self.session.get("/api/comics?id=-1&fields=id") as resp:
            print(await resp.json())
            latest_id = (await resp.json())["latest_id"]
            return latest_id

    async def get_comics_ids(self):
        async with self.session.get("/api/comics?fields=id") as resp:
            print(resp)

    async def get_ru_comics_ids(self):
        async with self.session.get("/api/comics?lang=ru&fields=id") as resp:
            print(resp)

    async def get_comic_data_by_id(self, comic_id):
        async with self.session.get(f"/api/comics/{comic_id}") as resp:
            print(resp)

    async def get_comics_headlines_info_by_title(self, title):
        async with self.session.get(f"/api/comics?title={title}&fields=id,title,img_url") as resp:
            print(resp)

    async def toggle_spec_status(self):
        async with self.session.put("/api/comics") as resp:
            print(resp)


api = ApiClient()
