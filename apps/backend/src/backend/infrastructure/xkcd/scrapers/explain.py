# mypy: disable-error-code="union-attr"

import importlib.resources
import logging
import re

from bs4 import BeautifulSoup, Tag
from rich.progress import Progress
from yarl import URL

from backend.infrastructure.downloader import Downloader
from backend.infrastructure.http_client import AsyncHttpClient
from backend.infrastructure.xkcd.pbar import CustomProgressBar
from backend.infrastructure.xkcd.scrapers.base import BaseScraper
from backend.infrastructure.xkcd.scrapers.dtos import LimitParams, XkcdExplanationScrapedData
from backend.infrastructure.xkcd.scrapers.exceptions import ExtractError, ScrapeError
from backend.infrastructure.xkcd.utils import run_concurrently

logger = logging.getLogger(__name__)

NUMBER_FROM_URL_PATTERN = re.compile(r"(\d*?): .*?")
TRANSCRIPT_TEXT_MAX_LENGTH = 25_000


class XkcdExplainScraper(BaseScraper):
    _BASE_URL = URL("https://explainxkcd.com/")

    def __init__(self, client: AsyncHttpClient, downloader: Downloader) -> None:
        super().__init__(client=client, downloader=downloader)
        self._bad_tags = self._load_bad_tags()
        self._cached_latest_number = None

    async def fetch_one(self, number: int) -> XkcdExplanationScrapedData | None:
        url = self._BASE_URL / f"wiki/index.php/{number}"
        soup = await self._get_soup(url)

        if soup.find("div", {"class": "noarticletext"}):
            return None

        try:
            explanation_data = XkcdExplanationScrapedData(
                number=number,
                explain_url=self._extract_real_url(soup),
                tags=self._extract_tags(soup),
                raw_transcript=self._extract_transcript_html(soup),
            )
        except Exception as err:
            raise ScrapeError(url) from err
        else:
            return explanation_data

    async def fetch_many(
        self,
        limits: LimitParams,
        progress: Progress,
    ) -> list[XkcdExplanationScrapedData]:
        numbers = list(range(limits.start, limits.end + 1))

        return await run_concurrently(
            data=numbers,
            coro=self.fetch_one,
            chunk_size=limits.chunk_size,
            delay=limits.delay,
            pbar=CustomProgressBar(
                progress,
                f"Explanation data scraping... \\[{self._BASE_URL}]",
                len(numbers),
            ),
        )

    async def fetch_recently_updated_numbers(self, days: int = 1, limit: int = 500) -> list[int]:
        url = (
            self._BASE_URL
            / "wiki/index.php/Special:RecentChanges"
            % {
                "namespace": "0",
                "days": days,
                "limit": limit,
            }
        )

        soup = await self._get_soup(url)

        titles = [tag["title"] for tag in soup.find_all("a", {"class": "mw-changeslist-title"})]

        numbers = set()
        for title in titles:
            match = re.match(NUMBER_FROM_URL_PATTERN, title)
            if match:
                numbers.add(int(match.group(1)))

        return list(numbers)

    def _extract_real_url(self, soup: BeautifulSoup) -> URL:
        if rel_url := soup.find(id="ca-nstab-main").find("a").get("href"):
            return self._BASE_URL.joinpath(str(rel_url)[1:], encoded=True)
        raise ExtractError

    def _extract_tags(self, soup: BeautifulSoup) -> list[str]:
        tags = set()

        if li_tags := soup.find(id="mw-normal-catlinks").find_all("li"):
            tag_lower_set = set()
            for tag in [li.text for li in li_tags]:
                tag_lower = tag.lower()
                if not any(bad_word in tag_lower for bad_word in self._bad_tags):
                    if tag_lower not in tag_lower_set:
                        tags.add(tag)
                    tag_lower_set.add(tag_lower)

        return sorted(tags)

    def _extract_transcript_html(self, soup: BeautifulSoup) -> str:
        transcript_html = ""

        if transcript_tag := soup.find(id="Transcript"):
            if transcript_header := transcript_tag.parent:
                buffer, length = "", 0
                for tag in transcript_header.find_next_siblings():
                    if isinstance(tag, Tag):
                        if tag.get("id") == "Discussion" or tag.name in ("h1", "h2"):
                            break
                        if tag.name == "table" and "transcript is incomplete" in tag.get_text():
                            continue

                        tag_as_text = str(tag)
                        length += len(tag_as_text)

                        if length > TRANSCRIPT_TEXT_MAX_LENGTH:  # №2131
                            buffer = ""
                            break

                        buffer += tag_as_text

                transcript_html = buffer

        return transcript_html.replace("<p><br/></p>", "")

    def _load_bad_tags(self) -> set[str]:
        bad_tags = set()

        try:
            with importlib.resources.open_text("assets", "bad_tags.txt") as f:
                bad_tags = {line.lower() for line in f.read().splitlines() if line}
        except FileNotFoundError:
            logger.warning("Loading bad tags failed: File not found.")

        return bad_tags
