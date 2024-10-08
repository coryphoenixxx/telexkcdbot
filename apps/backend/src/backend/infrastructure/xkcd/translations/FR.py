# mypy: disable-error-code="union-attr, no-any-return"

import ast
import re
from dataclasses import dataclass, field

from yarl import URL

from backend.infrastructure.downloader import Downloader
from backend.infrastructure.xkcd import BaseScraper
from backend.infrastructure.xkcd.dtos import XkcdTranslationScrapedData
from backend.infrastructure.xkcd.exceptions import ScrapeError


@dataclass(slots=True)
class XkcdFRScraper(BaseScraper):
    BASE_URL = URL("https://xkcd.arnaud.at")
    downloader: Downloader
    cached_number_data_map: dict[int, list[str]] = field(init=False)

    def __post_init__(self) -> None:
        self.cached_number_data_map = {}

    async def fetch_one(self, number: int) -> XkcdTranslationScrapedData | None:
        number_data_map = await self.fetch_number_data_map()
        data = number_data_map.get(number)

        if not data:
            return None

        url = self.BASE_URL / str(number)

        try:
            translation_data = XkcdTranslationScrapedData(
                number=number,
                source_url=url,
                title=data[0],
                tooltip=data[1],
                image_path=await self.downloader.download(
                    url=self.BASE_URL / f"comics/{number}.jpg"
                ),
                language="FR",
            )
        except Exception as err:
            raise ScrapeError(url) from err
        else:
            return translation_data

    async def fetch_number_data_map(self) -> dict[int, list[str]]:
        if not self.cached_number_data_map:
            url = self.BASE_URL / "assets/index-IqkHua2R.js"
            soup = await self._get_soup(url)

            text = re.search(
                pattern=re.compile(r"const ic=(\{.*?})", re.DOTALL),
                string=soup.text,
            ).group(1)

            self.cached_number_data_map = ast.literal_eval(text)

        return self.cached_number_data_map
