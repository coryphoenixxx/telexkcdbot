import re

from bs4 import BeautifulSoup
from shared.http_client import HttpClient
from yarl import URL

from scraper.dtos import XkcdTranslationData
from scraper.scrapers.base import BaseScraper


class XkcdESScraper(BaseScraper):
    _BASE_URL = URL("https://es.xkcd.com/")

    def __init__(self, client: HttpClient, limit: int | None = None):
        super().__init__(client=client)
        self._limit = limit

    async def fetch_one(
        self,
        url: URL,
        from_: int,
        to_: int,
        progress_bar=None,
    ) -> XkcdTranslationData | None:
        soup = await self._get_soup(url)

        number = self._extract_number(soup)

        if not number:
            return

        if number < from_ or number > to_:
            return

        data = XkcdTranslationData(
            number=number,
            source_link=url,
            title=self._extract_title(soup),
            tooltip=self._extract_tooltip(soup),
            image_url=self._extract_image_url(soup),
            transcript_raw="",
            translator_comment="",
        )

        if data.title == "Geografía":  # fix: https://es.xkcd.com/strips/geografia/
            data.number = 1472

        if progress_bar:
            progress_bar()

        return data

    async def fetch_all_links(self) -> list[URL]:
        url = self._BASE_URL.joinpath("archive/")
        soup = await self._get_soup(url)

        link_tags = soup.find("div", {"id": "archive-ul"}).find_all("a")
        links = [self._BASE_URL.joinpath(tag.get("href")[3:]) for tag in link_tags]

        return links

    def _extract_number(self, soup: BeautifulSoup) -> int | None:
        xkcd_link = soup.find("div", {"id": "middleContent"}).find_all("a")[-1].get("href")

        match = re.match(
            pattern=re.compile(r".*xkcd.com/(.*)"),
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
        return self._BASE_URL.joinpath(src[6:])
