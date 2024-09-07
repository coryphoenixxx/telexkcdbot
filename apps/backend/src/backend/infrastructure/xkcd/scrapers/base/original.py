import html
import logging
import re
from datetime import datetime as dt

from rich.progress import Progress
from yarl import URL

from backend.infrastructure.downloader import Downloader
from backend.infrastructure.http_client import AsyncHttpClient
from backend.infrastructure.http_client.dtos import HTTPStatusCodes
from backend.infrastructure.xkcd.pbar import CustomProgressBar
from backend.infrastructure.xkcd.scrapers import BaseScraper
from backend.infrastructure.xkcd.scrapers.dtos import (
    LimitParams,
    XkcdOriginalScrapedData,
)
from backend.infrastructure.xkcd.scrapers.exceptions import ScraperError
from backend.infrastructure.xkcd.utils import run_concurrently

logger = logging.getLogger(__name__)


HTML_TAG_PATTERN = re.compile(r"<.*?>")
X2_IMAGE_URL_PATTERN = re.compile(r"//(.*?) 2x")
IMAGE_URL_PATTERN = re.compile(r"https://imgs.xkcd.com/comics/(.*?).(jpg|jpeg|png|webp|gif)")


class XkcdOriginalScraper(BaseScraper):
    _BASE_URL = URL("https://xkcd.com/")

    def __init__(self, client: AsyncHttpClient, downloader: Downloader) -> None:
        super().__init__(client=client, downloader=downloader)
        self._cached_latest_number = None

    async def fetch_latest_number(self) -> int:
        if not self._cached_latest_number:
            async with self._client.safe_get(url=self._BASE_URL / "info.0.json") as response:
                json_data = await response.json()
            self._cached_latest_number = json_data["num"]

        return self._cached_latest_number

    async def fetch_one(self, number: int) -> XkcdOriginalScrapedData | None:
        if number > await self.fetch_latest_number() or number <= 0:
            return None

        url = self._BASE_URL / f"{number!s}/"

        if number == HTTPStatusCodes.NOT_FOUND_404:
            data = XkcdOriginalScrapedData(
                number=404,
                xkcd_url=url,
                title="404: Not Found",
                publication_date=self._build_date(y="2008", m="04", d="01"),
            )
        else:
            async with self._client.safe_get(url / "info.0.json") as response:
                json_data = await response.json()

            try:
                click_url, large_image_page_url = self._process_link(json_data["link"])

                image_url = (
                        await self._fetch_large_image_url(large_image_page_url)
                        or await self._fetch_2x_image_url(url)
                        or self._process_image_url(json_data["img"])
                )

                data = XkcdOriginalScrapedData(
                    number=json_data["num"],
                    xkcd_url=url,
                    title=self._process_title(json_data["title"]),
                    publication_date=self._build_date(
                        y=json_data["year"],
                        m=json_data["month"],
                        d=json_data["day"],
                    ),
                    click_url=click_url,
                    tooltip=json_data["alt"],
                    image_path=await self._downloader.download(image_url) if image_url else None,
                    is_interactive=bool(json_data.get("extra_parts")),
                )
            except Exception as err:
                raise ScraperError(url) from err

        return data

    async def fetch_many(
        self,
        limits: LimitParams,
        progress: Progress,
    ) -> list[XkcdOriginalScrapedData]:
        numbers = list(range(limits.start, limits.end + 1))

        return await run_concurrently(
            data=numbers,
            coro=self.fetch_one,
            chunk_size=limits.chunk_size,
            delay=limits.delay,
            pbar=CustomProgressBar(
                progress,
                f"Original data scraping... \\[{self._BASE_URL}]",
                len(numbers),
            ),
        )

    async def _fetch_large_image_url(self, url: URL | None) -> URL | None:
        # №657, №681, №802, №832, №850 ...
        if not url:
            return None

        if IMAGE_URL_PATTERN.match(str(url)):
            return url

        soup = await self._get_soup(url)

        if img_tag := soup.find("img"):
            if large_image_url := img_tag.get("src"):
                return URL(large_image_url)
        return None

    async def _fetch_2x_image_url(self, xkcd_url: URL) -> URL | None:
        soup = await self._get_soup(xkcd_url)

        if img_tags := soup.css.select("div#comic img"):
            if srcset := img_tags[0].get("srcset"):
                if match := X2_IMAGE_URL_PATTERN.search(srcset):
                    return URL("https://" + match.group(1).strip())
        return None

    def _process_title(self, title: str) -> str:
        # №259, №472
        if HTML_TAG_PATTERN.match(title):
            return HTML_TAG_PATTERN.sub("", title)

        return html.unescape(title)

    def _process_link(self, link: str | None) -> tuple[URL | None, URL | None]:
        click_url, large_image_page_url = None, None

        if link:
            link = URL(link)
            if "large" in link.path:
                large_image_page_url = link
            elif "980/huge" in link.path:
                large_image_page_url = URL("https://imgs.xkcd.com/comics/money_huge.png")
            elif link.scheme:
                click_url = link

        return click_url, large_image_page_url

    def _process_image_url(self, url: str) -> URL | None:
        return URL(url) if IMAGE_URL_PATTERN.match(url) else None

    def _build_date(self, y: str, m: str, d: str) -> dt.date:
        return dt.strptime(f"{int(y)}-{int(m):02d}-{int(d):02d}", "%Y-%m-%d")  # noqa: DTZ007
