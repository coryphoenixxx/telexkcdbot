import asyncio
import csv
import sys
from dataclasses import astuple
from datetime import date
from pathlib import Path
from typing import Optional, Sequence

import aiohttp
from aiohttp import ClientConnectorError
from bs4 import BeautifulSoup
from googletrans import Translator
from loguru import logger
from src.bot.middlewares.localization import _
from src.config import RU_COMIC_DATA_DIR
from src.models import RuComicData, TotalComicData, XKCDComicData
from tqdm import tqdm


class ComicsDataGetter:
    def __init__(self) -> None:
        # Specific comics cannot be displayed correctly in Telegram
        self.ru_comics_ids: Sequence[int] = tuple()
        self._default_specific_comic_ids: set = {
            498,
            826,
            880,
            887,
            980,
            1037,
            1110,
            1190,
            1193,
            1331,
            1335,
            1350,
            1416,
            1506,
            1525,
            1608,
            1663,
            1975,
            2067,
            2131,
            2198,
            2288,
            2445,
        }
        self._translator: Translator = Translator()

        self._ru_comics_data_dict: dict = {}
        self._path_to_ru_comic_data: Path = RU_COMIC_DATA_DIR

    @staticmethod
    async def get_xkcd_latest_comic_id() -> int:
        url = "https://xkcd.com/info.0.json"
        async with aiohttp.ClientSession() as session:
            comic_json = (await session.get(url)).json()
        return int((await comic_json).get("num"))

    @staticmethod
    def _url_fixer(url: str, comic_id: int) -> str:
        """Telegram doesn't upload original image, so let replace their urls."""

        correct_urls = {
            109: "https://www.explainxkcd.com/wiki/images/5/50/spoiler_alert.png",
            658: "https://www.explainxkcd.com/wiki/images/1/1c/orbitals.png",
            2522: "https://www.explainxkcd.com/wiki/images/b/bf/two_factor_security_key.png",
        }

        if comic_id in correct_urls.keys():
            return correct_urls[comic_id]
        return url

    @staticmethod
    async def _get_soup(url: str) -> Optional[BeautifulSoup]:
        """Gets soup of explanation text for further parsing"""

        attempts = 3
        for attempt in range(attempts):
            async with aiohttp.ClientSession() as session:
                try:
                    response = await session.get(url)
                except ClientConnectorError:
                    await asyncio.sleep(1)
                    continue
                else:
                    if response.ok:
                        content = await response.content.read()
                        return BeautifulSoup(content, "lxml")

        logger.error(f"Couldn't get soup for {url} after 3 attempts!")
        return None

    def _process_path(self, comic_id: str) -> str:
        """
        Russian comics images have .png or .jpg extension.
        So let get the actual filename and make a relational path for writing it in the database.
        """

        filename = list((self._path_to_ru_comic_data / "images").glob(f"{comic_id}.*"))[0].name
        return "static/ru_comics_data/images/" + filename

    def _translate_to_ru(self, text: str) -> str:
        result: str = self._translator.translate(text, src="en", dest="ru").text
        return result

    def retrieve_from_csv_to_dict(self) -> None:
        """Retrieve Russian translation info from local storage csv file to dictionary"""

        with open(self._path_to_ru_comic_data / "data.csv", "r", encoding="utf-8") as csv_file:
            csv_reader = csv.DictReader(csv_file, delimiter=",")
            for row in tqdm(list(csv_reader), file=sys.stdout):
                comic_id = int(row["comic_id"])
                self._ru_comics_data_dict[comic_id] = RuComicData(
                    ru_title=row["ru_title"],
                    ru_img_url=self._process_path(row["comic_id"]),
                    ru_comment=row["ru_comment"],
                    has_ru_translation=True,
                )

    async def get_xkcd_comic_data_by_id(self, comic_id: int) -> XKCDComicData:
        """Gets English comic data from xkcd.com"""

        if comic_id == 404:
            return XKCDComicData()  # 404 comic doesn't exist, so return default
        else:
            async with aiohttp.ClientSession() as session:
                url = f"https://xkcd.com/{comic_id}/info.0.json"
                response = await session.get(url)
                comic_json = await response.json()

            # Telegram considers '<' and '>' as html tag symbols, so let remove them
            comment = comic_json.get("alt").replace("<", "").replace(">", "").strip()  # TODO: regexp

            return XKCDComicData(
                comic_id=comic_id,
                title=comic_json.get("safe_title") if comic_json.get("safe_title") else "...",
                img_url=self._url_fixer(comic_json.get("img"), comic_id),
                comment=comment if comment else "...",
                public_date=date(
                    day=int(comic_json.get("day")),
                    month=int(comic_json.get("month")),
                    year=int(comic_json.get("year")),
                ),
                is_specific=True if comic_id in self._default_specific_comic_ids else False,
            )

    async def get_ru_comic_data_by_id(self, comic_id: int) -> RuComicData:
        """Gets russian comic data from dictionary by comic id"""

        ru_comic_data = self._ru_comics_data_dict.get(comic_id)
        if not ru_comic_data:
            return RuComicData()  # return empty
        return self._ru_comics_data_dict[comic_id]

    async def get_total_comic_data(self, comic_id: int) -> TotalComicData:
        """Unions all comic data"""

        xkcd_comic_data = await self.get_xkcd_comic_data_by_id(comic_id)
        ru_comic_data = await self.get_ru_comic_data_by_id(comic_id)
        return TotalComicData(*(astuple(xkcd_comic_data) + astuple(ru_comic_data)))

    async def get_explanation(self, comic_id: int, url: str) -> str:
        no_explanation_text: str = _(
            "❗ <b>There's no explanation yet or explainxkcd.com is unavailable. Try it later.</b>"
        )

        try:
            soup = await self._get_soup(url)
            if soup:
                try:
                    first_p = soup.find_all("div", {"class": "mw-parser-output"})[-1].find("p")
                except AttributeError:
                    pass
                else:
                    text: str = first_p.text + "\n"
                    for el in first_p.find_next_siblings()[:20]:
                        if el.name in ("p", "li"):
                            text = text + el.text.strip() + "\n\n"

                    # Telegram considers '<' and '>' as html tag symbols, so let remove them
                    text = text[:1500].strip().replace("<", "").replace(">", "")

                    if not text:
                        return no_explanation_text
                    return text

        except Exception as err:
            logger.error(f"Error in get_explanation() for {comic_id}: {err}")

        return no_explanation_text

    async def get_ru_explanation(self, comic_id: int, url: str) -> str:
        en_explanation_text = await self.get_explanation(comic_id, url)

        # Don't translate if couldn't get explanation
        if "❗" in en_explanation_text:
            return en_explanation_text

        await asyncio.sleep(2)  # Protection from potential ban by Google

        try:
            ru_explanation_text = self._translate_to_ru(en_explanation_text)
        except Exception as err:
            logger.error(f"Couldn't get translated explanation for {comic_id}: {err}")
            return en_explanation_text
        else:
            return ru_explanation_text

    def clean(self) -> None:
        self.ru_comics_ids = tuple(self._ru_comics_data_dict.keys())

        # Remove unused data in the future (_ru_comics_data_dict takes 30MB of RAM)
        del self._ru_comics_data_dict
        del self._path_to_ru_comic_data


comics_data_getter = ComicsDataGetter()
