import asyncio
import html
import logging
import re

from bs4 import BeautifulSoup, Tag
from rich.progress import Progress
from shared.http_client import AsyncHttpClient
from yarl import URL

from scraper.dtos import XkcdBaseScrapedData, XkcdExplainScrapedData, XkcdOriginScrapedData
from scraper.scrapers.base import BaseScraper
from scraper.scrapers.exceptions import ScraperError
from scraper.types import LimitParams
from scraper.utils import ProgressBar, run_concurrently

logger = logging.getLogger(__name__)


HTML_TAG_PATTERN = re.compile(r"<.*?>")


def build_date(y: str, m: str, d: str) -> str:
    return f"{int(y)}-{int(m):02d}-{int(d):02d}"


class XkcdOriginScraper(BaseScraper):
    _XKCD_URL = URL("https://xkcd.com/")
    _EXPLAIN_XKCD_URL = URL("https://explainxkcd.com/wiki/index.php/")

    def __init__(self, client: AsyncHttpClient):
        super().__init__(client=client)
        self._bad_tags = self._load_bad_tags()
        self._cached_latest_number = None

    async def fetch_latest_number(self) -> int:
        if not self._cached_latest_number:
            async with self._client.safe_get(url=self._XKCD_URL / "info.0.json") as response:
                json_data = await response.json()
            self._cached_latest_number = json_data["num"]

        return self._cached_latest_number

    async def fetch_one(
        self,
        number: int,
        pbar: ProgressBar | None = None,
    ) -> XkcdOriginScrapedData | None:
        try:
            async with asyncio.TaskGroup() as tg:
                fetch_origin_task = tg.create_task(self.fetch_base_data(number))
                fetch_explain_task = tg.create_task(self.fetch_explain_data(number))
        except* Exception as errors:
            for exc in errors.exceptions:
                raise exc
        else:
            origin_data, explain_data = fetch_origin_task.result(), fetch_explain_task.result()

            if not origin_data:
                return None

            if pbar:
                pbar.advance()

            return XkcdOriginScrapedData(
                number=origin_data.number,
                publication_date=origin_data.publication_date,
                xkcd_url=origin_data.xkcd_url,
                title=origin_data.title,
                tooltip=origin_data.tooltip,
                link_on_click=origin_data.link_on_click,
                is_interactive=origin_data.is_interactive,
                image_url=origin_data.image_url,
                explain_url=explain_data.explain_url if explain_data else None,
                tags=explain_data.tags if explain_data else [],
                transcript_raw=explain_data.transcript_raw if explain_data else "",
            )

    async def fetch_many(
        self,
        limits: LimitParams,
        progress: Progress,
    ) -> list[XkcdOriginScrapedData]:
        numbers = list(range(limits.start, limits.end + 1))

        return await run_concurrently(
            data=numbers,
            coro=self.fetch_one,
            limits=limits,
            pbar=ProgressBar(progress, "Origin data scraping...", len(numbers)),
        )

    async def fetch_base_data(self, number: int) -> XkcdBaseScrapedData | None:
        if number > await self.fetch_latest_number() or number <= 0:
            return None

        xkcd_url = self._XKCD_URL / (str(number) + "/")

        if number == 404:
            return XkcdBaseScrapedData(
                number=404,
                xkcd_url=xkcd_url,
                title="404: Not Found",
                publication_date="2008-04-01",
            )
        else:
            async with self._client.safe_get(xkcd_url / "info.0.json") as response:
                json_data = await response.json()

            try:
                link_on_click, large_image_page_url = self._process_link(json_data["link"])

                return XkcdBaseScrapedData(
                    number=json_data["num"],
                    xkcd_url=xkcd_url,
                    title=self._process_title(json_data["title"]),
                    publication_date=build_date(
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
            except Exception as err:
                raise ScraperError(xkcd_url) from err

    async def fetch_explain_data(self, number: int) -> XkcdExplainScrapedData | None:
        explain_url = self._EXPLAIN_XKCD_URL / str(number)
        soup = await self._get_soup(explain_url)

        if soup.find("div", {"class": "noarticletext"}):
            return None

        try:
            return XkcdExplainScrapedData(
                explain_url=explain_url,
                tags=self._extract_tags(soup),
                transcript_raw=self._extract_transcript_html(soup),
            )
        except Exception as err:
            raise ScraperError(explain_url) from err

    async def _fetch_large_image_url(self, url: URL | None) -> URL | None:
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

    def _process_title(self, title: str) -> str:
        # №259, №472
        match = re.match(HTML_TAG_PATTERN, title)
        if match:
            return re.sub(HTML_TAG_PATTERN, "", title)

        return html.unescape(title)

    def _process_link(self, link: str | None) -> tuple[URL | None, URL | None]:
        link_on_click, large_image_page_url = None, None

        if link:
            link = URL(link)
            if "large" in link.path:
                large_image_page_url = link
            elif link.scheme:
                link_on_click = link

        return link_on_click, large_image_page_url

    def _process_image_url(self, url: str) -> URL | None:
        match = re.match(
            pattern="https://imgs.xkcd.com/comics/(.*?).(jpg|jpeg|png|webp|gif)",
            string=url,
        )
        if match:
            return URL(url)

    def _extract_tags(self, soup: BeautifulSoup) -> list[str]:
        tags = set()

        li_tags = soup.find(id="mw-normal-catlinks").find_all("li")
        if li_tags:
            tag_lower_set = set()
            for tag in [li.text for li in li_tags]:
                tag_lower = tag.lower()
                if not any(bad_word in tag_lower for bad_word in self._bad_tags):
                    if tag_lower not in tag_lower_set:
                        tags.add(tag)
                    tag_lower_set.add(tag_lower)

        return sorted(tags)

    def _extract_transcript_html(self, soup: BeautifulSoup) -> str:
        transcript_html = ""

        transcript_tag: Tag = soup.find(id="Transcript")

        if transcript_tag:
            transcript_header = transcript_tag.parent
            if transcript_header:
                temp, length = "", 0
                for tag in transcript_header.find_next_siblings():  # type: Tag
                    tag_name = tag.name
                    if tag.get("id") == "Discussion" or tag_name in ("h1", "h2"):
                        break
                    elif tag_name == "table" and "transcript is incomplete" in tag.get_text():
                        continue
                    else:
                        tag_as_text = str(tag)
                        length += len(tag_as_text)

                        if length > 25_000:
                            temp = ""
                            break
                        else:
                            temp += tag_as_text

                transcript_html = temp

        return transcript_html

    def _load_bad_tags(self) -> set[str]:
        bad_tags = set()

        try:
            with open("../data/bad_tags.txt") as f:
                bad_tags = {line.lower() for line in f.read().splitlines() if line}
        except FileNotFoundError:
            logger.warning("Loading bad tags failed: File not found.")

        return bad_tags
