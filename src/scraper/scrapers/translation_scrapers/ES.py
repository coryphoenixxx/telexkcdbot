import re

from bs4 import BeautifulSoup
from rich.progress import Progress
from scraper.dtos import XkcdScrapedTranslationData
from scraper.scrapers.base import BaseScraper
from scraper.scrapers.exceptions import ScraperError
from scraper.types import LimitParams
from scraper.utils import ProgressBar, run_concurrently
from shared.http_client import AsyncHttpClient
from shared.types import LanguageCode
from yarl import URL

XKCD_NUMBER_PATTERN = re.compile(r".*xkcd.com/(.*)")


class XkcdESScraper(BaseScraper):
    _BASE_URL = URL("https://es.xkcd.com/")

    def __init__(self, client: AsyncHttpClient):
        super().__init__(client=client)

    async def fetch_one(
        self,
        url: URL,
        range_: tuple[int, int],
        pbar: ProgressBar | None = None,
    ) -> XkcdScrapedTranslationData | None:
        soup = await self._get_soup(url)

        number = self._extract_number(soup)

        if not number or number < range_[0] or number > range_[1]:
            return

        try:
            data = XkcdScrapedTranslationData(
                number=number,
                source_link=url,
                title=self._extract_title(soup),
                tooltip=self._extract_tooltip(soup),
                image_url=self._extract_image_url(soup),
                language=LanguageCode.ES,
            )
        except Exception as err:
            raise ScraperError(url) from err

        if data.title == "Geografía":  # fix: https://es.xkcd.com/strips/geografia/
            data.number = 1472

        if pbar:
            pbar.advance()

        return data

    async def fetch_many(
        self,
        limits: LimitParams,
        progress: Progress,
    ) -> list[XkcdScrapedTranslationData]:
        urls = await self.fetch_all_links()

        return await run_concurrently(
            data=urls,
            coro=self.fetch_one,
            limits=limits,
            range_=(limits.start, limits.end),
            pbar=ProgressBar(progress, "Spanish translations scraping..."),
        )

    async def fetch_all_links(self) -> list[URL]:
        url = self._BASE_URL / "archive/"
        soup = await self._get_soup(url)

        link_tags = soup.find("div", {"id": "archive-ul"}).find_all("a")
        links = [self._BASE_URL / tag.get("href")[3:] for tag in link_tags]

        return links

    def _extract_number(self, soup: BeautifulSoup) -> int | None:
        xkcd_link = soup.find("div", {"id": "middleContent"}).find_all("a")[-1].get("href")

        match = re.match(
            pattern=XKCD_NUMBER_PATTERN,
            string=xkcd_link,
        )
        if match:
            return int(match.group(1).replace("/", ""))

    def _extract_title(self, soup) -> str:
        return soup.find("div", {"id": "middleContent"}).find("h1").text

    def _extract_tooltip(self, soup) -> str:
        return soup.find("img", {"class": "strip"}).get("title")

    def _extract_image_url(self, soup) -> URL:
        src = soup.find("img", {"class": "strip"}).get("src")
        return self._BASE_URL / src[6:]
