from aiohttp import ClientPayloadError, ClientResponse  # noqa: F401
from bs4 import BeautifulSoup
from shared.http_client import HttpClient
from yarl import URL


class BaseScraper:
    def __init__(self, client: HttpClient) -> None:
        self._client = client

    async def _get_soup(self, url: URL, **kwargs):
        while True:
            try:
                async with self._client.safe_get(url=url, **kwargs) as response:
                    html = await response.content.read()
                    break
            except ClientPayloadError:
                continue

        return BeautifulSoup(html, "lxml")
