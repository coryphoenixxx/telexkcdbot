from bs4 import BeautifulSoup
from yarl import URL

from shared.http_client import HttpClient


class BaseScraper:
    def __init__(
        self,
        client: HttpClient,
    ):
        self._client = client

    async def _get_soup(self, url: URL):
        async with self._client.safe_get(url=url) as response:
            html = await response.text()

        return BeautifulSoup(html, "lxml")
