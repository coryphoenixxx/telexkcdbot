# mypy: disable-error-code="union-attr"

import asyncio
from collections.abc import Iterable

from bs4 import BeautifulSoup
from rich.progress import Progress
from yarl import URL

from backend.infrastructure.downloader import Downloader
from backend.infrastructure.http_client import AsyncHttpClient
from backend.infrastructure.xkcd.pbar import CustomProgressBar
from backend.infrastructure.xkcd.scrapers import BaseScraper
from backend.infrastructure.xkcd.scrapers.dtos import LimitParams, XkcdTranslationScrapedData
from backend.infrastructure.xkcd.scrapers.exceptions import ExtractError, ScrapeError
from backend.infrastructure.xkcd.utils import run_concurrently


class XkcdZHScraper(BaseScraper):
    _BASE_URL = URL("https://xkcd.in")

    def __init__(self, client: AsyncHttpClient, downloader: Downloader) -> None:
        super().__init__(client=client, downloader=downloader)

    async def fetch_one(self, url: URL) -> XkcdTranslationScrapedData:
        soup = await self._get_soup(url)

        try:
            tooltip, translator_comment = self._extract_tooltip_and_translator_comment(soup)

            translation_data = XkcdTranslationScrapedData(
                number=self._extract_number_from_url(url),
                source_url=url,
                title=self._extract_title(soup),
                tooltip=tooltip,
                image_path=await self._downloader.download(url=self._extract_image_url(soup)),
                translator_comment=translator_comment,
                language="ZH",
            )
        except Exception as err:
            raise ScrapeError(url=url) from err
        else:
            return translation_data

    async def fetch_many(
        self,
        limits: LimitParams,
        progress: Progress,
    ) -> list[XkcdTranslationScrapedData]:
        links = [
            link
            for link in await self.fetch_all_links()
            if limits.start <= int(str(link).split("=")[-1]) <= limits.end
        ]

        return await run_concurrently(
            data=links,
            coro=self.fetch_one,
            chunk_size=limits.chunk_size,
            delay=limits.delay,
            pbar=CustomProgressBar(
                progress,
                f"Chinese translations scraping... \\[{self._BASE_URL}]",
                len(links),
            ),
        )

    async def fetch_all_links(self) -> list[URL]:
        soup = await self._get_soup(self._BASE_URL)
        page_range = await self._get_page_range(soup)

        return await self._collect_all_links(page_range)

    async def _get_page_range(self, soup: BeautifulSoup) -> Iterable[int]:
        navigation_buttons = soup.find("ul", {"class": "pagination"}).find_all("li")
        last_page_num = int(navigation_buttons[-1].find("a").get("href").split("=")[-1])

        return range(last_page_num, 0, -1)

    async def _collect_all_links(self, nums: Iterable[int]) -> list[URL]:
        all_links = []

        page_urls = [self._BASE_URL % {"lg": "cn", "page": num} for num in nums]

        try:
            async with asyncio.TaskGroup() as tg:
                tasks = [tg.create_task(self._fetch_one_page_links(url)) for url in page_urls]
        except* Exception as errors:
            for _ in errors.exceptions:
                raise
        else:
            for task in tasks:
                all_links += task.result()

        return all_links

    async def _fetch_one_page_links(self, url: URL) -> list[URL]:
        soup = await self._get_soup(url)

        a_tags = soup.find("div", {"id": "strip_list"}).find_all("a")

        return [URL(str(self._BASE_URL) + a.get("href")) for a in reversed(a_tags)]

    def _extract_number_from_url(self, url: URL) -> int:
        return int(str(url).split("=")[-1])

    def _extract_title(self, soup: BeautifulSoup) -> str:
        return soup.find("div", {"id": "content"}).find("h1").text.strip()

    def _extract_tooltip_and_translator_comment(self, soup: BeautifulSoup) -> tuple[str, str]:
        caption = soup.find("div", {"class": "comic-details"}).text

        if "\n\n" in caption:
            tooltip, translator_comment = caption.split("\n\n", maxsplit=1)
        else:
            tooltip, translator_comment = caption, ""

        return tooltip.strip(), translator_comment.strip()

    def _extract_image_url(self, soup: BeautifulSoup) -> URL:
        image_url_rel_path = soup.find("div", {"class": "comic-body"}).find("img").get("src")
        if image_url_rel_path:
            return self._BASE_URL / str(image_url_rel_path)[1:]
        raise ExtractError
