import asyncio
import html
import logging
import re

from aiohttp import ClientResponse
from bs4 import BeautifulSoup, Tag
from yarl import URL

from scraper.dtos import XKCDExplainData, XKCDOriginData, XKCDFullScrapedData
from scraper.scrapers.base import BaseScraper
from shared.http_client import HttpClient


class XKCDScraper(BaseScraper):
    _XKCD_URL = URL("https://xkcd.com/")
    _EXPLAIN_XKCD_URL = URL("https://explainxkcd.com/wiki/index.php/")

    def __init__(self, client: HttpClient):
        super().__init__(client=client)
        self._bad_tags = self._load_bad_tags()

    async def fetch_latest_number(self) -> int:
        async with self._client.safe_get(url=self._XKCD_URL.joinpath("info.0.json")) as response:
            json_data = await response.json()

        return json_data["num"]

    async def fetch_one(self, number: int) -> XKCDFullScrapedData:
        fetch_origin_task = asyncio.create_task(self.fetch_origin_data(number))
        fetch_explain_task = asyncio.create_task(self.fetch_explain_data(number))

        try:
            origin_data: XKCDOriginData = await fetch_origin_task
            explain_data: XKCDExplainData = await fetch_explain_task
        except Exception as err:
            logging.error(err)
            raise err

        return XKCDFullScrapedData(
            number=origin_data.number,
            publication_date=origin_data.publication_date,
            xkcd_url=origin_data.xkcd_url,
            title=origin_data.title,
            tooltip=origin_data.tooltip,
            link_on_click=origin_data.link_on_click,
            is_interactive=origin_data.is_interactive,
            image_url=origin_data.image_url,
            explain_url=explain_data.explain_url,
            tags=explain_data.tags,
            transcript=explain_data.transcript,
        )

    async def fetch_origin_data(self, number: int) -> XKCDOriginData:
        xkcd_url = self._XKCD_URL.joinpath(str(number))

        if number == 404:
            return XKCDOriginData(
                number=404,
                xkcd_url=xkcd_url,
                title="404: Not Found",
                publication_date="2008-04-01",
                link_on_click=None,
                tooltip="",
                image_url=None,
                is_interactive=False,
            )
        else:
            async with self._client.safe_get(
                xkcd_url.joinpath("info.0.json")
            ) as response:  # type: ClientResponse
                json_data = await response.json()

            link_on_click, large_image_page_url = self._process_link(json_data["link"])

            data = XKCDOriginData(
                number=json_data["num"],
                xkcd_url=xkcd_url,
                title=self._process_title(json_data["title"]),
                publication_date=self._build_date(
                    y=json_data["year"],
                    m=json_data["month"],
                    d=json_data["day"],
                ),
                link_on_click=link_on_click,
                tooltip=json_data["alt"],
                image_url=(
                    await self._fetch_large_image_url(large_image_page_url)
                    or await self._fetch_2x_image_url(xkcd_url)
                    or self._process_image_url(json_data["img"])
                ),
                is_interactive=bool(json_data.get("extra_parts")),
            )

            return data

    async def fetch_explain_data(self, number: int) -> XKCDExplainData:
        url = self._EXPLAIN_XKCD_URL.joinpath(str(number))
        soup = await self._get_soup(url)

        return XKCDExplainData(
            explain_url=url,
            tags=self._extract_tags(soup),
            transcript=self._extract_transcript_html(soup),
        )

    async def _fetch_large_image_url(self, url: URL | None,) -> URL | None:
        # №657, №681, №802, №832, №850 ...
        if not url:
            return None

        soup = await self._get_soup(url)

        img_tag = soup.find("img")
        if img_tag:
            large_image_url = img_tag.get("src")
            if large_image_url:
                return URL(large_image_url)

    async def _fetch_2x_image_url(self, xkcd_url: URL) -> URL | None:
        x2_image_url = None

        soup = await self._get_soup(xkcd_url)

        img_tags = soup.css.select("div#comic img")

        if img_tags:
            srcset = img_tags[0].get("srcset")
            if srcset:
                match = re.search(pattern="//(.*?) 2x", string=srcset)
                if match:
                    x2_image_url = URL("https://" + match.group(1).strip())

        return x2_image_url

    @staticmethod
    def _process_title(title: str):  # №259, №472
        if any(c in title for c in ("<", ">")):
            return re.sub(re.compile("<.*?>"), "", title)
        return html.unescape(title)

    @staticmethod
    def _process_link(link: str) -> tuple[URL | None, URL | None]:
        link_on_click, large_image_page_url = None, None
        if link:
            link = URL(link)
            if "large" in link.path:
                large_image_page_url = link
            elif link.scheme:
                link_on_click = link

        return link_on_click, large_image_page_url

    @staticmethod
    def _build_date(y: str, m: str, d: str) -> str:
        return f"{int(y)}-{int(m):02d}-{int(d):02d}"

    @staticmethod
    def _process_image_url(url: str) -> URL | None:
        match = re.match(
            pattern="https://imgs.xkcd.com/comics/(.*?).(jpg|jpeg|png|webp|gif)",
            string=url,
        )
        if match:
            return URL(url)

    def _extract_tags(self, soup: BeautifulSoup) -> list[str]:
        li_tags = soup.find(id="mw-normal-catlinks").find_all("li")

        tags = set()
        for tag in [li.text for li in li_tags]:
            if not any(
                bad_word in tag.lower() for bad_word in self._bad_tags
            ) and tag.lower() not in {t.lower() for t in tags}:
                tags.add(tag)

        return sorted(tags)

    @staticmethod
    def _extract_transcript_html(soup: BeautifulSoup) -> str:
        transcript_html = ""

        transcript_tag: Tag = soup.find(id="Transcript")

        if transcript_tag:
            transcript_header = transcript_tag.parent
            if transcript_header:

                for tag in transcript_header.find_next_siblings():  # type: Tag
                    tag_name = tag.name
                    if tag.get("id") == "Discussion" or tag_name in ("h1", "h2"):
                        break
                    elif tag_name == "table" and "This transcript is incomplete" in tag.get_text():
                        continue
                    else:
                        transcript_html += str(tag)

        return transcript_html

    @staticmethod
    def _load_bad_tags() -> set[str]:
        bad_tags = set()

        try:
            with open("../data/bad_tags.txt") as f:
                bad_tags = {line for line in f.read().splitlines() if line}
        except FileNotFoundError:
            logging.error("Loading bad tag error. File not found.")

        return bad_tags
