import re

from bs4 import BeautifulSoup
from rich.progress import Progress
from scraper.dtos import XkcdTranslationData
from scraper.pbar import ProgressBar
from scraper.scrapers.base import BaseScraper
from scraper.scrapers.exceptions import ScraperError
from scraper.types import LimitParams
from scraper.utils import run_concurrently
from shared.http_client import AsyncHttpClient
from shared.types import LanguageCode
from yarl import URL


class XkcdDEScraper(BaseScraper):
    _BASE_URL = URL("https://xkcde.dapete.net/")

    def __init__(self, client: AsyncHttpClient):
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

    async def fetch_one(
        self,
        number: int,
        pbar: ProgressBar | None = None,
    ) -> XkcdTranslationData | None:
        if number == 404:
            return

        url = self._BASE_URL / (str(number) + "/")
        soup = await self._get_soup(url, allow_redirects=False)

        if not len(soup):
            return

        try:
            translation = XkcdTranslationData(
                number=number,
                source_link=url,
                title=self._extract_title(soup),
                tooltip=self._extract_tooltip(soup),
                image=await self._extract_image_url(soup),
                translator_comment=self._extract_comment(soup),
                language=LanguageCode.DE,
            )
        except Exception as err:
            raise ScraperError(url) from err

        if pbar:
            pbar.advance()

        return translation

    async def fetch_many(
        self,
        limits: LimitParams,
        progress: Progress,
    ) -> list[XkcdTranslationData]:
        latest_num = await self.fetch_latest_number()

        numbers = [n for n in range(limits.start, limits.end + 1) if n <= latest_num]

        return await run_concurrently(
            data=numbers,
            coro=self.fetch_one,
            limits=limits,
            pbar=ProgressBar(
                progress,
                f"Deutsch translations scraping...\n({self._BASE_URL}):",
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
