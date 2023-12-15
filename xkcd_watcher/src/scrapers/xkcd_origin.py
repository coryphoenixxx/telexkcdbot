import asyncio
from json import JSONDecodeError

import aiohttp
from aiohttp import ContentTypeError


class XkcdOriginScraper:
    xkcd_json_base_url = "https://xkcd.com/{comic_id}/info.0.json"

    def __init__(self, throttler: asyncio.Semaphore):
        self._throttler = throttler

    async def fetch_json(self, session: aiohttp.ClientSession, comic_id: int):
        async with self._throttler, session.get(
            self.xkcd_json_base_url.format(comic_id=comic_id),
        ) as response:  # type: aiohttp.ClientResponse
            try:
                comic_json_data = await response.json()
                comic_json_data["link"]
                comic_json_data["news"]

                # if "extra_parts" in comic_json_data:
                #     print(f"{comic_id} -- NOT 11")

                # if link:
                #     print(f"{comic_id} -- link {link}")
                #
                # if news:
                #     print(f"{comic_id} -- news {news}")

            except (JSONDecodeError, ContentTypeError):
                ...
            except Exception:
                ...
