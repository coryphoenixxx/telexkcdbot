# mypy: disable-error-code="union-attr"

import re
from dataclasses import dataclass

from bs4 import BeautifulSoup
from yarl import URL

from backend.infrastructure.downloader import Downloader
from backend.infrastructure.http_client.http_codes import HTTPStatusCodes
from backend.infrastructure.xkcd import BaseScraper
from backend.infrastructure.xkcd.dtos import XkcdTranslationScrapedData
from backend.infrastructure.xkcd.exceptions import ExtractError, ScrapeError


@dataclass(slots=True)
class XkcdDEScraper(BaseScraper):
    BASE_URL = URL("https://xkcde.dapete.net/")
    downloader: Downloader

    async def fetch_latest_number(self) -> int:
        soup = await self._get_soup(self.BASE_URL)

        xkcd_link = soup.find("p", {"class": "center"}).find("a").get("href")
        if xkcd_link:
            match = re.match(pattern=re.compile(r".*.xkcd.com/(.*)/"), string=str(xkcd_link))
            return int(match.group(1))

        raise ScrapeError(self.BASE_URL)

    async def fetch_one(self, number: int) -> XkcdTranslationScrapedData | None:
        if number == HTTPStatusCodes.NOT_FOUND_404:
            return None

        url = self.BASE_URL / (str(number) + "/")
        soup = await self._get_soup(url, allow_redirects=False)

        if not len(soup):
            return None

        try:
            translation = XkcdTranslationScrapedData(
                number=number,
                source_url=url,
                title=self._extract_title(soup),
                tooltip=self._extract_tooltip(soup),
                image_path=await self.downloader.download(url=await self._extract_image_url(soup)),
                translator_comment=self._extract_comment(soup),
                language="DE",
            )
        except Exception as err:
            raise ScrapeError(url) from err
        else:
            return translation

    def _extract_title(self, soup: BeautifulSoup) -> str:
        title_block = soup.find("h2", {"class": "comictitle"})
        title_block.span.decompose()

        return title_block.text.strip()

    def _extract_tooltip(self, soup: BeautifulSoup) -> str:
        return soup.find("figcaption").text

    async def _extract_image_url(self, soup: BeautifulSoup) -> URL:
        image_rel_path = None

        if large_version_block := soup.find("div", {"id": "large_version"}):
            if large_image_page_url := large_version_block.find("a").get("href"):
                soup = await self._get_soup(self.BASE_URL / str(large_image_page_url)[1:])
                image_rel_path = soup.find("img").get("src")
        else:
            image_rel_path = soup.find("figure", {"id": "comic"}).find("img").get("src")

        if image_rel_path:
            return self.BASE_URL / str(image_rel_path)[1:]
        raise ExtractError

    def _extract_comment(self, soup: BeautifulSoup) -> str:
        comment = ""
        comment_block = soup.find("div", {"id": "comments"})

        if comment_block:
            comment = comment_block.find("p").text

        return comment
