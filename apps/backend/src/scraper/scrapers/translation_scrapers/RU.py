import re

from bs4 import BeautifulSoup, Tag
from rich.progress import Progress
from shared.http_client import AsyncHttpClient
from yarl import URL

from scraper.dtos import XkcdTranslationData
from scraper.my_types import LimitParams
from scraper.pbar import ProgressBar
from scraper.scrapers.base import BaseScraper
from scraper.scrapers.exceptions import ScraperError
from scraper.utils import run_concurrently

DIV_CONTENT_PATTERN = re.compile(r"<div.*?>(.*?)</div>", flags=re.DOTALL)

REPEATED_BR_TAG_PATTERN = re.compile(r"(<br/>| )\1{2,}")


class XkcdRUScraper(BaseScraper):
    _BASE_URL = URL("https://xkcd.ru/")
    _NUM_LIST_URL = _BASE_URL / "num"

    def __init__(self, client: AsyncHttpClient) -> None:
        super().__init__(client=client)

    async def get_all_nums(self) -> list[int]:
        soup = await self._get_soup(self._NUM_LIST_URL)

        return self._extract_all_nums(soup)

    async def fetch_one(self, number: int) -> XkcdTranslationData:
        url = self._BASE_URL / (str(number) + "/")
        soup = await self._get_soup(url)

        try:
            data = XkcdTranslationData(
                number=number,
                source_url=url,
                title=self._extract_title(soup),
                tooltip=self._extract_tooltip(soup),
                image=self._extract_image_url(soup),
                raw_transcript=self._extract_transcript(soup),
                translator_comment=self._extract_comment(soup),
                language="RU",
            )
        except Exception as err:
            raise ScraperError(url) from err

        return data

    async def fetch_many(
        self,
        limits: LimitParams,
        progress: Progress,
    ) -> list[XkcdTranslationData]:
        all_nums = await self.get_all_nums()

        filtered_numbers = [n for n in all_nums if limits.start <= n <= limits.end]

        return await run_concurrently(
            data=filtered_numbers,
            coro=self.fetch_one,
            chunk_size=limits.chunk_size,
            delay=limits.delay,
            pbar=ProgressBar(
                progress,
                f"Russian translations scraping...\n\\[{self._BASE_URL}]",
                len(filtered_numbers),
            ),
        )

    def _extract_all_nums(self, soup: BeautifulSoup) -> list[int]:
        return [int(num.text) for num in soup.find_all("li", {"class": "real"})]

    def _extract_title(self, soup: BeautifulSoup) -> str:
        return soup.find("h1").text

    def _extract_tooltip(self, soup: BeautifulSoup) -> str:
        return soup.find("div", {"class": "comics_text"}).text

    def _extract_image_url(self, soup: BeautifulSoup) -> URL:
        image_url = soup.find("div", {"class": "main"}).find("img").get("src")

        image_tags = soup.find_all(name="a")
        for tag in image_tags:
            src = tag.get("href")
            if "large" in src:
                image_url = src

        return URL(image_url)

    def _extract_transcript(self, soup: BeautifulSoup) -> str:
        transcript_block = soup.find("div", {"class": "transcription"})
        return self._extract_tag_content(
            tag=transcript_block,
            pattern=DIV_CONTENT_PATTERN,
        )

    def _extract_comment(self, soup: BeautifulSoup) -> str:
        comment_block = soup.find("div", {"class": "comment"})

        return self._extract_tag_content(
            tag=comment_block,
            pattern=DIV_CONTENT_PATTERN,
        )

    def _extract_tag_content(self, tag: Tag, pattern: str | re.Pattern[str]) -> str:
        content = ""
        if tag:
            match = re.match(
                pattern=pattern,
                string=str(tag),
            )
            if match:
                content = re.sub(
                    pattern=REPEATED_BR_TAG_PATTERN,
                    repl="",
                    string=match.group(1),
                )

        return content.strip()
