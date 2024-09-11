from typing import Any

from aiohttp import ClientPayloadError
from bs4 import BeautifulSoup
from yarl import URL

from backend.infrastructure.downloader import Downloader
from backend.infrastructure.http_client import AsyncHttpClient
from backend.infrastructure.xkcd.scrapers.exceptions import ScrapeError


class BaseScraper:
    def __init__(
        self,
        client: AsyncHttpClient,
        downloader: Downloader,
    ) -> None:
        self._client = client
        self._downloader = downloader

    async def _get_soup(self, url: URL, **kwargs: Any) -> BeautifulSoup:
        for _ in range(3):
            try:
                async with self._client.safe_get(url=url, **kwargs) as response:
                    html = await response.content.read()
                    break
            except ClientPayloadError:
                continue
        else:
            raise ScrapeError(url)

        return BeautifulSoup(html, "lxml")
