import re

from bs4 import BeautifulSoup, Tag
from rich.progress import Progress
from scraper.dtos import XkcdScrapedTranslationData
from scraper.scrapers.base import BaseScraper
from scraper.types import LimitParams
from scraper.utils import ProgressBar, run_concurrently
from shared.http_client import AsyncHttpClient
from shared.types import LanguageCode
from yarl import URL


class XkcdRUScraper(BaseScraper):
    _BASE_URL = URL("https://xkcd.ru/")
    _NUM_LIST_URL = _BASE_URL.joinpath("num")

    def __init__(self, client: AsyncHttpClient):
        super().__init__(client=client)

    async def get_all_nums(self) -> list[int]:
        soup = await self._get_soup(self._NUM_LIST_URL)

        return self._extract_nums(soup)

    async def fetch_one(
        self,
        number: int,
        pbar: ProgressBar | None = None,
    ) -> XkcdScrapedTranslationData:
        url = self._BASE_URL.joinpath(str(number) + "/")
        soup = await self._get_soup(url)

        data = XkcdScrapedTranslationData(
            number=number,
            source_link=url,
            title=self._extract_title(soup),
            tooltip=self._extract_tooltip(soup),
            image_url=self._extract_image_url(soup),
            transcript_raw=self._extract_transcript(soup),
            translator_comment=self._extract_comment(soup),
            language=LanguageCode.RU,
        )

        if pbar:
            pbar.advance()

        return data

    async def fetch_many(
        self,
        limits: LimitParams,
        progress: Progress,
    ) -> list[XkcdScrapedTranslationData]:
        all_nums = await self.get_all_nums()

        numbers = [n for n in all_nums if limits.start <= n <= limits.end]

        return await run_concurrently(
            data=numbers,
            coro=self.fetch_one,
            limits=limits,
            pbar=ProgressBar(progress, "Russian scraping...", len(numbers)),
        )

    def _extract_nums(self, soup: BeautifulSoup) -> list[int]:
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
        transcript_html = self._extract_tag_content(
            tag=transcript_block,
            pattern=r"<div.*?>(.*?)<\/div>",
        )

        return transcript_html

    def _extract_comment(self, soup: BeautifulSoup) -> str:
        comment_block = soup.find("div", {"class": "comment"})
        comment_html = self._extract_tag_content(
            tag=comment_block,
            pattern=r"<div.*?>(.*?)<\/div>",
        )

        return comment_html

    def _extract_tag_content(self, tag: Tag, pattern: str) -> str:
        content = ""
        if tag:
            match = re.match(
                pattern=pattern,
                string=str(tag),
                flags=re.DOTALL,
            )
            if match:
                content = re.sub(
                    pattern=r"(<br/>| )\1{2,}",
                    repl="",
                    string=match.group(1),
                )

        return content.strip()
