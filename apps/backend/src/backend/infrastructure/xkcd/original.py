# mypy: disable-error-code="union-attr"
import html
import re
from dataclasses import dataclass
from typing import ClassVar

from yarl import URL

from backend.domain.utils import cast_or_none
from backend.infrastructure.downloader import Downloader
from backend.infrastructure.http_client.http_codes import HTTPStatusCodes
from backend.infrastructure.xkcd import BaseScraper
from backend.infrastructure.xkcd.dtos import XkcdOriginalScrapedData
from backend.infrastructure.xkcd.exceptions import ScrapeError

HTML_TAG_PATTERN = re.compile(r"<.*?>")
IMAGE_URL_PATTERN = re.compile(r"https://imgs.xkcd.com/comics/(.*?).(jpg|jpeg|png|gif)")
IMAGE_X2_SRCSET_PATTERN = re.compile(r"//(imgs.xkcd.com/comics/[^ ]+_2x.png) 2x")
ENLARGED_IMAGE_PAGE_URL = re.compile(r"https://xkcd.com/\d+([_/])large/?")

KNOWN_ENLARGED_IMAGE_URLS = {
    256: "https://imgs.xkcd.com/comics/online_communities.png",
    273: "https://imgs.xkcd.com/comics/electromagnetic_spectrum.png",
    980: "https://imgs.xkcd.com/comics/money_huge.png",
    1799: "https://imgs.xkcd.com/comics/bad_map_projection_time_zones_2x.png",
}


@dataclass(slots=True)
class XkcdOriginalScraper(BaseScraper):
    BASE_URL: ClassVar[URL] = URL("https://xkcd.com")

    downloader: Downloader

    async def fetch_latest_number(self) -> int:
        async with self.client.safe_get(url=self.BASE_URL / "info.0.json") as response:
            json_data = await response.json()
        return int(json_data["num"])

    async def fetch_one(self, number: int) -> XkcdOriginalScrapedData:
        url = self.BASE_URL / f"{number}/"

        if number == HTTPStatusCodes.NOT_FOUND_404:
            return XkcdOriginalScrapedData(
                number=404,
                xkcd_url=url,
                title="404: Not Found",
                publication_date=self._build_date(y="2008", m="04", d="01"),
            )

        try:
            async with self.client.safe_get(url / "info.0.json") as response:
                json_data = await response.json()

            click_url, enlarged_image_url = await self._handle_link(number, json_data["link"])

            image_url = (
                enlarged_image_url
                or await self._fetch_2x_image_url(url)
                or self._handle_image_url(json_data["img"])
            )

            return XkcdOriginalScrapedData(
                number=json_data["num"],
                xkcd_url=url,
                title=self._clean_title(json_data["title"]),
                publication_date=self._build_date(
                    y=json_data["year"],
                    m=json_data["month"],
                    d=json_data["day"],
                ),
                click_url=cast_or_none(str, click_url),
                tooltip=json_data["alt"],
                image_path=await self.downloader.download(image_url) if image_url else None,
                is_interactive=bool(json_data.get("extra_parts")),
            )
        except Exception as err:
            raise ScrapeError(url) from err

    def _clean_title(self, title: str) -> str:
        # №259, №472
        if HTML_TAG_PATTERN.match(title):
            return HTML_TAG_PATTERN.sub("", title)

        return html.unescape(title)

    async def _handle_link(
        self,
        number: int,
        link_raw: str | None,
    ) -> tuple[URL | None, URL | None]:
        click_url, enlarged_image_url = None, None

        if link_raw:
            if known_url := KNOWN_ENLARGED_IMAGE_URLS.get(number):
                enlarged_image_url = URL(known_url)
            # №657, №681, №802, №832, №850 ...
            elif ENLARGED_IMAGE_PAGE_URL.match(link_raw):
                soup = await self._get_soup(URL(link_raw))
                if enlarged_image_url_src := soup.find("img").get("src"):
                    enlarged_image_url = URL(enlarged_image_url_src)
            # №1506, №1525
            elif URL(link_raw).with_scheme("https") != self.BASE_URL / f"{number}/":
                click_url = URL(link_raw)

        return click_url, enlarged_image_url

    async def _fetch_2x_image_url(self, xkcd_url: URL) -> URL | None:
        soup = await self._get_soup(xkcd_url)

        if img_tags := soup.css.select("div#comic img"):
            if srcset := img_tags[0].get("srcset"):
                if match := IMAGE_X2_SRCSET_PATTERN.search(srcset):
                    return URL("https://" + match.group(1).strip())

        return None

    def _handle_image_url(self, image_url: str) -> URL | None:
        return URL(image_url) if IMAGE_URL_PATTERN.match(image_url) else None

    def _build_date(self, y: str, m: str, d: str) -> str:
        return f"{int(y)}-{int(m):02d}-{int(d):02d}"
