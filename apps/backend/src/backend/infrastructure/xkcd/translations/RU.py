# mypy: disable-error-code="union-attr, no-any-return"

import re
from dataclasses import dataclass

from bs4 import BeautifulSoup
from bs4.element import NavigableString, Tag
from yarl import URL

from backend.infrastructure.downloader import Downloader
from backend.infrastructure.xkcd import BaseScraper
from backend.infrastructure.xkcd.dtos import XkcdTranslationScrapedData
from backend.infrastructure.xkcd.exceptions import ExtractError, ScrapeError

DIV_CONTENT_PATTERN = re.compile(r"<div.*?>(.*?)</div>", flags=re.DOTALL)

REPEATED_BR_TAG_PATTERN = re.compile(r"(<br/>| )\1{2,}")


@dataclass(slots=True)
class XkcdRUScraper(BaseScraper):
    downloader: Downloader
    BASE_URL = URL("https://xkcd.ru")
    NUM_LIST_URL = BASE_URL / "num"

    async def get_all_nums(self) -> list[int]:
        soup = await self._get_soup(self.NUM_LIST_URL)

        return self._extract_all_nums(soup)

    async def fetch_one(self, number: int) -> XkcdTranslationScrapedData:
        url = self.BASE_URL / (str(number) + "/")
        soup = await self._get_soup(url)

        try:
            translation_data = XkcdTranslationScrapedData(
                number=number,
                source_url=url,
                title=self._extract_title(soup),
                tooltip=self._extract_tooltip(soup),
                image_path=await self.downloader.download(url=self._extract_image_url(soup)),
                transcript=self._extract_transcript(soup),
                translator_comment=self._extract_comment(soup),
                language="RU",
            )
        except Exception as err:
            raise ScrapeError(url) from err
        else:
            return translation_data

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

        if image_url:
            return URL(str(image_url))
        raise ExtractError

    def _extract_transcript(self, soup: BeautifulSoup) -> str:
        if transcript_block := soup.find("div", {"class": "transcription"}):
            return self._extract_tag_content(
                tag=transcript_block,
                pattern=DIV_CONTENT_PATTERN,
            )
        return ""

    def _extract_comment(self, soup: BeautifulSoup) -> str:
        if comment_block := soup.find("div", {"class": "comment"}):
            return self._extract_tag_content(
                tag=comment_block,
                pattern=DIV_CONTENT_PATTERN,
            )
        return ""

    def _extract_tag_content(
        self,
        tag: Tag | NavigableString,
        pattern: str | re.Pattern[str],
    ) -> str:
        if tag and (match := re.match(pattern=pattern, string=str(tag))):
            return re.sub(
                pattern=REPEATED_BR_TAG_PATTERN,
                repl="",
                string=match.group(1),
            ).strip()
        return ""
