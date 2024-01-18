import aiohttp
from bs4 import BeautifulSoup

from src.utils import get_throttler, retry_get


class ExplainXkcdScraper:
    BASE_URL = "https://explainxkcd.com/"

    def __init__(self, session: aiohttp.ClientSession):
        self._session = session
        self._throttler = get_throttler(10)
        self._bad_tags = (
            "comics",
            "citation needed",
            "xkcd.com",
            "livejournal",
            "characters with hats",
            "multiple cueballs",
            "incomplete explanations",
            "checkered paper",
        )

    async def fetch_tags(self, issue_number: int) -> list[str]:
        async with retry_get(
            session=self._session,
            throttler=self._throttler,
            url=f"{self.BASE_URL}/{issue_number}",
        ) as response:
            page = await response.text()

        soup = BeautifulSoup(page, "lxml")
        tag_li_tags = soup.find(id="mw-normal-catlinks").find_all("li")

        return self._validate_tags([li_tag.text for li_tag in tag_li_tags])

    def _validate_tags(self, tags: list[str]) -> list[str]:
        result = set()
        for tag in tags:
            if not any(
                bad_word in tag.lower() for bad_word in self._bad_tags
            ) and tag.lower() not in {t.lower() for t in result}:
                result.add(tag)
        return list(result)
