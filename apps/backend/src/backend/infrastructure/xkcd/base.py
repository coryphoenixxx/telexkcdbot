from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from aiohttp import ClientPayloadError
from bs4 import BeautifulSoup
from yarl import URL

from backend.infrastructure.http_client import AsyncHttpClient
from backend.infrastructure.xkcd.exceptions import ScrapeError


@dataclass(slots=True)
class BaseScraper(ABC):
    client: AsyncHttpClient

    @abstractmethod
    async def fetch_one(self, *args: Any, **kwargs: Any) -> Any: ...

    async def _get_soup(self, url: URL, **kwargs: Any) -> BeautifulSoup:
        for _ in range(3):
            try:
                async with self.client.safe_get(url=url, **kwargs) as response:
                    return BeautifulSoup(await response.content.read(), "lxml")
            except ClientPayloadError:  # noqa: PERF203
                continue
        raise ScrapeError(url)
