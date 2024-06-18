from aiohttp import ClientPayloadError
from bs4 import BeautifulSoup
from shared.http_client import AsyncHttpClient
from yarl import URL


class BaseScraper:
    def __init__(self, client: AsyncHttpClient) -> None:
        self._client = client

    async def _get_soup(self, url: URL, **kwargs) -> BeautifulSoup:
        for _ in range(3):
            try:
                async with self._client.safe_get(url=url, **kwargs) as response:
                    html = await response.content.read()
                    break
            except ClientPayloadError:
                continue

        return BeautifulSoup(html, "lxml")
