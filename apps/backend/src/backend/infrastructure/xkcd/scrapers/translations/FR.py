import ast
import re

from rich.progress import Progress
from yarl import URL

from backend.infrastructure.downloader import Downloader
from backend.infrastructure.http_client import AsyncHttpClient
from backend.infrastructure.xkcd.pbar import CustomProgressBar
from backend.infrastructure.xkcd.scrapers import BaseScraper
from backend.infrastructure.xkcd.scrapers.dtos import LimitParams, XkcdTranslationScrapedData
from backend.infrastructure.xkcd.scrapers.exceptions import ScraperError
from backend.infrastructure.xkcd.utils import run_concurrently


class XkcdFRScraper(BaseScraper):
    _BASE_URL = URL("https://xkcd.arnaud.at/")

    def __init__(self, client: AsyncHttpClient, downloader: Downloader) -> None:
        super().__init__(client=client, downloader=downloader)
        self._cached_number_data_map = None

    async def fetch_one(self, number: int) -> XkcdTranslationScrapedData | None:
        number_data_map = await self._get_number_data_map()
        data = number_data_map.get(number)

        if not data:
            return None

        url = self._BASE_URL / str(number)

        try:
            translation = XkcdTranslationScrapedData(
                number=number,
                source_url=url,
                title=data[0],
                tooltip=data[1],
                image_path=await self._downloader.download(
                    url=self._BASE_URL / f"comics/{number}.jpg"
                ),
                language="FR",
            )
        except Exception as err:
            raise ScraperError(url) from err

        return translation

    async def fetch_many(
        self,
        limits: LimitParams,
        progress: Progress | None = None,
    ) -> list[XkcdTranslationScrapedData]:
        number_data_map = await self._get_number_data_map()
        latest_num = max(number_data_map.keys())

        return await run_concurrently(
            data=[n for n in range(limits.start, limits.end + 1) if n <= latest_num],
            coro=self.fetch_one,
            chunk_size=limits.chunk_size,
            delay=limits.delay,
            pbar=CustomProgressBar(
                progress,
                f"French translations scraping... \\[{self._BASE_URL}]",
            ),
        )

    async def _get_number_data_map(self) -> dict[int, list[str, str]]:
        if not self._cached_number_data_map:
            url = self._BASE_URL / "assets/index-IqkHua2R.js"
            soup = await self._get_soup(url)

            text = re.search(
                pattern=re.compile(r"const ic=(\{.*?})", re.DOTALL),
                string=soup.text,
            ).group(1)

            self._cached_number_data_map = ast.literal_eval(text)

        return self._cached_number_data_map
