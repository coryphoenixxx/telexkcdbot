from aiohttp import ClientPayloadError
from bs4 import BeautifulSoup
from yarl import URL

from backend.infrastructure.downloader import Downloader
from backend.infrastructure.http_client import AsyncHttpClient


class BaseScraper:
    def __init__(
        self,
        client: AsyncHttpClient,
        downloader: Downloader | None = None,
    ) -> None:
        self._client = client
        self._downloader = downloader

    async def _get_soup(self, url: URL, **kwargs) -> BeautifulSoup:
        for _ in range(3):
            try:
                async with self._client.safe_get(url=url, **kwargs) as response:
                    html = await response.content.read()
                    break
            except ClientPayloadError:
                continue

        return BeautifulSoup(html, "lxml")
