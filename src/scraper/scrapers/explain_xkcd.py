import asyncio

from bs4 import BeautifulSoup
from scraper.dtos import ExplainXkcdDTO
from shared.http_client import HttpClient
from yarl import URL


class ExplainXkcdScraper:
    _BASE_URL = URL("https://explainxkcd.com/")

    def __init__(
        self,
        client: HttpClient,
        throttler: asyncio.Semaphore | None = asyncio.Semaphore(5),
    ):
        self._client = client
        self._bad_tags = self._load_bad_tags()
        self._throttler = throttler

    async def fetch_one(self, number: int) -> ExplainXkcdDTO:
        soup = await self._fetch_soup(number)

        return ExplainXkcdDTO(
            tags=self.extract_tags(soup),
        )

    def extract_tags(self, soup: BeautifulSoup) -> list[str]:
        li_tags = soup.find(id="mw-normal-catlinks").find_all("li")
        return self._validate_tags([li.text for li in li_tags])

    async def _fetch_soup(self, number: int) -> BeautifulSoup:
        async with self._client.safe_get(url=self._BASE_URL.joinpath(str(number))) as response:
            html = await response.text()

        return BeautifulSoup(html, "lxml")

    def _validate_tags(self, tags: list[str]) -> list[str]:
        result = set()
        for tag in tags:
            if not any(
                bad_word in tag.lower() for bad_word in self._bad_tags
            ) and tag.lower() not in {t.lower() for t in result}:
                result.add(tag)

        return list(result)

    @staticmethod
    def _load_bad_tags() -> set[str]:
        with open("../data/bad_tags.txt") as f:
            return {line for line in f.read().splitlines() if line}
