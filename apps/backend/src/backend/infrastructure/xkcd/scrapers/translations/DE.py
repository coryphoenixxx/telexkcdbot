import re

from bs4 import BeautifulSoup
from rich.progress import Progress
from yarl import URL

from backend.infrastructure.http_client import AsyncHttpClient
from backend.infrastructure.http_client.dtos import HTTPStatusCodes
from backend.infrastructure.xkcd.pbar import CustomProgressBar
from backend.infrastructure.xkcd.scrapers import BaseScraper
from backend.infrastructure.xkcd.scrapers.dtos import LimitParams, XkcdTranslationScrapedData
from backend.infrastructure.xkcd.scrapers.exceptions import ScraperError
from backend.infrastructure.xkcd.utils import run_concurrently


class XkcdDEScraper(BaseScraper):
    _BASE_URL = URL("https://xkcde.dapete.net/")

    def __init__(self, client: AsyncHttpClient) -> None:
        super().__init__(client=client)

    async def fetch_latest_number(self) -> int:
        soup = await self._get_soup(self._BASE_URL)

        xkcd_link = soup.find("p", {"class": "center"}).find("a").get("href")

        return int(
            re.match(
                pattern=re.compile(r".*.xkcd.com/(.*)/"),
                string=xkcd_link,
            ).group(1),
        )

    async def fetch_one(self, number: int) -> XkcdTranslationScrapedData | None:
        if number == HTTPStatusCodes.NOT_FOUND_404:
            return None

        url = self._BASE_URL / (str(number) + "/")
        soup = await self._get_soup(url, allow_redirects=False)

        if not len(soup):
            return None

        try:
            translation = XkcdTranslationScrapedData(
                number=number,
                source_url=url,
                title=self._extract_title(soup),
                tooltip=self._extract_tooltip(soup),
                image_url=await self._extract_image_url(soup),
                translator_comment=self._extract_comment(soup),
                language="DE",
            )
        except Exception as err:
            raise ScraperError(url) from err

        return translation

    async def fetch_many(
        self,
        limits: LimitParams,
        progress: Progress,
    ) -> list[XkcdTranslationScrapedData]:
        latest_num = await self.fetch_latest_number()

        numbers = [n for n in range(limits.start, limits.end + 1) if n <= latest_num]

        return await run_concurrently(
            data=numbers,
            coro=self.fetch_one,
            chunk_size=limits.chunk_size,
            delay=limits.delay,
            pbar=CustomProgressBar(
                progress,
                f"Deutsch translations scraping...\n\\[{self._BASE_URL}]",
            ),
        )

    def _extract_title(self, soup: BeautifulSoup) -> str:
        title_block = soup.find("h2", {"class": "comictitle"})
        title_block.span.decompose()

        return title_block.text.strip()

    def _extract_tooltip(self, soup: BeautifulSoup) -> str:
        return soup.find("figcaption").text

    async def _extract_image_url(self, soup: BeautifulSoup) -> URL:
        large_version_block = soup.find("div", {"id": "large_version"})

        if large_version_block:
            large_image_page_url = large_version_block.find("a").get("href")
            soup = await self._get_soup(self._BASE_URL / large_image_page_url[1:])
            image_rel_path = soup.find("img").get("src")
        else:
            image_rel_path = soup.find("figure", {"id": "comic"}).find("img").get("src")

        return self._BASE_URL / image_rel_path[1:]

    def _extract_comment(self, soup: BeautifulSoup) -> str:
        comment = ""
        comment_block = soup.find("div", {"id": "comments"})

        if comment_block:
            comment = comment_block.find("p").text

        return comment
