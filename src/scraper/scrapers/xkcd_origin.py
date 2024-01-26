import re

from bs4 import BeautifulSoup
from scraper.dtos import Images, XkcdOriginDTO
from shared.http_client import HttpClient
from yarl import URL


class XkcdOriginScraper:
    _BASE_URL = URL("https://xkcd.com/")

    def __init__(
        self,
        client: HttpClient,
    ):
        self._client = client

    async def fetch_latest_number(
        self,
    ) -> int:
        async with self._client.safe_get(url=self._BASE_URL.joinpath("info.0.json")) as response:
            json_data = await response.json()

        return json_data["num"]

    async def fetch_one(self, number: int) -> XkcdOriginDTO:
        xkcd_url = self._BASE_URL.joinpath(str(number))

        if number == 404:
            comic = XkcdOriginDTO(
                number=404,
                xkcd_url=xkcd_url,
                title="404: Not Found",
                publication_date="2008-04-01",
            )
        else:
            async with self._client.safe_get(xkcd_url.joinpath("info.0.json")) as response:
                json_data = await response.json()

            link_on_click, large_image_page_url = self._process_link(json_data["link"])

            comic = XkcdOriginDTO(
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
                images=Images(
                    default=self._process_image_url(json_data["img"]),
                    x2=await self._fetch_2x_image_url(xkcd_url),
                    large=await self._fetch_large_image_url(large_image_page_url),
                ),
                is_interactive=bool(json_data.get("extra_parts")),
            )

        return comic

    async def _fetch_large_image_url(self, url: URL | None) -> URL | None:
        if not url:
            return None

        async with self._client.safe_get(url=url) as response:
            html = await response.text()

        soup = BeautifulSoup(html, "lxml")

        large_image_url = soup.find("img").get("src")
        if large_image_url:
            return URL(large_image_url)

    async def _fetch_2x_image_url(self, xkcd_url: URL) -> URL | None:
        x2_image_url = None

        async with self._client.safe_get(url=xkcd_url) as response:
            html = await response.text()

        soup = BeautifulSoup(html, "lxml")

        img_tags = soup.css.select("div#comic img")
        if img_tags:
            srcset = img_tags[0].get("srcset")
            if srcset:
                match = re.search(
                    pattern="//(.*?) 2x",
                    string=srcset,
                )
                if match:
                    x2_image_url = URL("https://" + match.group(1).strip())

        return x2_image_url

    @staticmethod
    def _process_title(title: str):
        if ">" in title:
            return re.sub(re.compile("<.*?>"), "", title)
        return title

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
