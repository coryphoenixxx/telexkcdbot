# mypy: disable-error-code="union-attr"

import re
from dataclasses import dataclass, field

from bs4 import BeautifulSoup
from yarl import URL

from backend.infrastructure.downloader import Downloader
from backend.infrastructure.xkcd import BaseScraper
from backend.infrastructure.xkcd.dtos import XkcdTranslationScrapedData
from backend.infrastructure.xkcd.exceptions import ExtractError, ScrapeError

XKCD_NUMBER_PATTERN = re.compile(r".*xkcd.com/(.*)")


@dataclass(slots=True)
class XkcdESScraper(BaseScraper):
    BASE_URL = URL("https://es.xkcd.com/")
    downloader: Downloader
    all_links: list[URL] = field(init=False)

    async def fetch_one(
        self,
        url: URL,
        filter_numbers: set[int] | None = None,
    ) -> XkcdTranslationScrapedData | None:
        soup = await self._get_soup(url)

        number = self._extract_number(soup)

        if not number or (filter_numbers and number not in filter_numbers):
            return None

        try:
            translation_data = XkcdTranslationScrapedData(
                number=number,
                source_url=url,
                title=self._extract_title(soup),
                tooltip=self._extract_tooltip(soup),
                image_path=await self.downloader.download(url=self._extract_image_url(soup)),
                language="ES",
            )
            if translation_data.title == "Geografía":  # fix: https://es.xkcd.com/strips/geografia/
                translation_data.number = 1472
        except Exception as err:
            raise ScrapeError(url) from err
        else:
            return translation_data

    async def fetch_all_links(self) -> list[URL]:
        url = self.BASE_URL / "archive/"
        soup = await self._get_soup(url)

        link_tags = soup.find("div", {"id": "archive-ul"}).find_all("a")

        return [self.BASE_URL / tag.get("href")[3:] for tag in link_tags]

    def _extract_number(self, soup: BeautifulSoup) -> int | None:
        xkcd_link = soup.find("div", {"id": "middleContent"}).find_all("a")[-1].get("href")

        if match := XKCD_NUMBER_PATTERN.match(xkcd_link):
            return int(match.group(1).replace("/", ""))
        return None

    def _extract_title(self, soup: BeautifulSoup) -> str:
        return soup.find("div", {"id": "middleContent"}).find("h1").text

    def _extract_tooltip(self, soup: BeautifulSoup) -> str:
        if tooltip := soup.find("img", {"class": "strip"}).get("title"):
            return str(tooltip)
        return ""

    def _extract_image_url(self, soup: BeautifulSoup) -> URL:
        if img_src := soup.find("img", {"class": "strip"}).get("src"):
            return self.BASE_URL / str(img_src)[6:]
        raise ExtractError
