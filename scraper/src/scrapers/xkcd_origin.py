import asyncio
import re

from bs4 import BeautifulSoup
from src.dtos import Images, XkcdOriginDTO
from src.utils import get_session, get_throttler, retry_get, value_or_none


class XkcdOriginScraper:
    BASE_URL = "https://xkcd.com/"
    COMIC_URL = BASE_URL + "{issue_number}/"
    JSON_URL_PART = "info.0.json"
    JSON_URL = COMIC_URL + JSON_URL_PART

    def __init__(self, q: asyncio.Queue):
        self._session = get_session(timeout=10)
        self._throttler = get_throttler(connections=20)
        self._result_queue = q

    async def get_latest_issue_number(
        self,
        close_session: bool = True,
    ) -> int:
        async with retry_get(
            session=self._session,
            url=self.BASE_URL + self.JSON_URL_PART,
        ) as response:
            json_data = await response.json()

        if close_session:
            await self._session.close()
        return json_data["num"]

    async def fetch(
        self,
        issue_number: int,
        close_session: bool = True,
    ) -> XkcdOriginDTO:
        xkcd_url = self.COMIC_URL.format(issue_number=issue_number)

        if issue_number == 404:
            return XkcdOriginDTO(
                issue_number=404,
                xkcd_url=xkcd_url,
                title="404: Not Found",
                publication_date="2008-04-01",
                images=Images(),
            )
        async with self._throttler, retry_get(
                session=self._session,
                url=self.JSON_URL.format(issue_number=issue_number),
            ) as response:
                json_data = await response.json()

        link_on_click, large_img_url = self._process_link(json_data["link"])

        comic = XkcdOriginDTO(
            issue_number=json_data["num"],
            xkcd_url=xkcd_url,
            title=self._process_title(json_data["title"]),
            publication_date=self._process_date(
                y=json_data["year"],
                m=json_data["month"],
                d=json_data["day"],
            ),
            link_on_click=link_on_click,
            tooltip=json_data["alt"],
            news=value_or_none(json_data["news"]),
            images=Images(
                default=json_data["img"],
                x2=await self._get_2x_image_url(xkcd_url),
                large=large_img_url,
            ),
            is_interactive=bool(json_data.get("extra_parts")),
        )

        if close_session:
            await self._session.close()

        await self._result_queue.put(comic)

        return comic

    async def fetch_many(self, start: int = 1, end: int | None = None) -> list[XkcdOriginDTO]:
        if not end:
            end = await self.get_latest_issue_number(close_session=False)

        async with asyncio.TaskGroup() as tg:
            tasks = [
                tg.create_task(self.fetch(i, close_session=False))
                for i in range(start, end + 1)
            ]

        await self._session.close()
        return [task.result() for task in tasks]

    @staticmethod
    def _process_title(title: str):
        if '>' in title:
            return re.sub(re.compile('<.*?>'), '', title)
        return title

    @staticmethod
    def _process_link(link: str) -> tuple[str, str]:
        link_on_click, large_image_url = None, None
        if link:
            if "large" in link:
                large_image_url = link
            else:
                link_on_click = link

        return link_on_click, large_image_url

    @staticmethod
    def _process_date(y: str, m: str, d: str) -> str:
        return f"{int(y)}-{int(m):02d}-{int(d):02d}"

    async def _get_2x_image_url(self, xkcd_url: str) -> str | None:
        x2_image_url = None

        async with retry_get(session=self._session, url=xkcd_url) as response:
            page = await response.text()

        soup = BeautifulSoup(page, "lxml")
        img_tags = soup.css.select("div#comic img")

        if img_tags:
            srcset = img_tags[0].get("srcset")
            if srcset:
                match = re.search(
                    pattern="//(.*?) 2x",
                    string=srcset,
                )
                if match:
                    x2_image_url = "https://" + match.group(1).strip()

        return x2_image_url
