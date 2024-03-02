import ast
import re

from rich.progress import Progress
from scraper.dtos import XkcdTranslationData
from scraper.pbar import ProgressBar
from scraper.scrapers.base import BaseScraper
from scraper.scrapers.exceptions import ScraperError
from scraper.types import LimitParams
from shared.http_client import AsyncHttpClient
from shared.types import LanguageCode
from yarl import URL


class XkcdFRScraper(BaseScraper):
    _BASE_URL = URL("https://xkcd.arnaud.at/")

    def __init__(self, client: AsyncHttpClient):
        super().__init__(client=client)
        self._cached_number_data_map = None

    async def fetch_one(
        self,
        number: int,
        pbar: ProgressBar | None = None,
    ) -> XkcdTranslationData | None:
        number_data_map = await self._get_number_data_map()
        data = number_data_map.get(number)

        if not data:
            return

        url = self._BASE_URL / str(number)

        try:
            translation = XkcdTranslationData(
                number=number,
                source_link=url,
                title=data[0],
                tooltip=data[1],
                image=self._BASE_URL / f"comics/{number}.jpg",
                language=LanguageCode.FR,
            )
        except Exception as err:
            raise ScraperError(url) from err

        if pbar:
            pbar.advance()

        return translation

    async def fetch_many(
        self,
        limits: LimitParams,
        progress: Progress | None = None,
    ) -> list[XkcdTranslationData]:
        number_data_map = await self._get_number_data_map()
        latest_num = sorted(number_data_map.keys())[-1]

        numbers = [n for n in range(limits.start, limits.end + 1) if n <= latest_num]

        pbar = (
            ProgressBar(
                progress,
                f"French translations scraping...\n({self._BASE_URL}):",
            )
            if progress
            else None
        )

        translations = []
        for num in numbers:
            translation = await self.fetch_one(num, pbar)
            if translation:
                translations.append(translation)

        if pbar:
            pbar.finish()

        return translations

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
