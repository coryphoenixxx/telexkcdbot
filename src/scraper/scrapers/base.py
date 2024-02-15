import logging

from aiohttp import ClientPayloadError, ClientResponse  # noqa: F401
from bs4 import BeautifulSoup
from shared.http_client import HttpClient
from yarl import URL


class BaseScraper:
    def __init__(
        self,
        client: HttpClient,
    ):
        self._client = client

    async def _get_soup(self, url: URL, **kwargs):
        while True:
            try:
                async with self._client.safe_get(
                    url=url,
                    **kwargs,
                ) as response:  # type: ClientResponse
                    html = await response.content.read()
                    break
            except ClientPayloadError:
                continue
            except Exception as err:
                logging.error(err)
                raise err

        return BeautifulSoup(html, "lxml")
