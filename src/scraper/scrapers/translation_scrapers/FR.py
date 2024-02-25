import ast
import re

from rich.progress import Progress
from scraper.dtos import XkcdScrapedTranslationData
from scraper.scrapers.base import BaseScraper
from scraper.types import LimitParams
from scraper.utils import ProgressBar
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
    ) -> XkcdScrapedTranslationData | None:
        number_data_map = await self._get_number_data_map()
        data = number_data_map.get(number)

        if not data:
            return None
        else:
            translation = XkcdScrapedTranslationData(
                number=number,
                source_link=self._BASE_URL / str(number),
                title=data[0],
                tooltip=data[1],
                image_url=self._BASE_URL / f"comics/{number}.jpg",
                transcript_raw="",
                translator_comment="",
                language=LanguageCode.FR,
            )

            if pbar:
                pbar.advance()

            return translation

    async def fetch_many(
        self,
        limits: LimitParams,
        progress: Progress | None = None,
    ) -> list[XkcdScrapedTranslationData]:
        number_data_map = await self._get_number_data_map()
        latest_num = sorted(number_data_map.keys())[-1]

        numbers = [n for n in range(limits.start, limits.end + 1) if n <= latest_num]

        pbar = ProgressBar(progress, "French scraping...") if progress else None

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
                pattern=re.compile(r"const ic=(\{.*?})", re.DOTALL | re.MULTILINE),
                string=soup.text,
            ).group(1)

            self._cached_number_data_map = ast.literal_eval(text)

        return self._cached_number_data_map
