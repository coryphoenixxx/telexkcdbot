# mypy: disable-error-code="union-attr"
import logging
import re
from dataclasses import dataclass

from bs4 import BeautifulSoup
from bs4.element import Tag
from yarl import URL

from backend.infrastructure.xkcd.base import BaseScraper
from backend.infrastructure.xkcd.dtos import XkcdExplainScrapedData
from backend.infrastructure.xkcd.exceptions import ExtractError, ScrapeError

logger = logging.getLogger(__name__)

NUMBER_FROM_URL_PATTERN = re.compile(r"(\d*?): .*?")
TRANSCRIPT_TEXT_MAX_LENGTH = 25_000


@dataclass(slots=True)
class XkcdExplainScraper(BaseScraper):
    BASE_URL = URL("https://explainxkcd.com/")
    bad_tags: set[str]

    async def fetch_one(self, number: int) -> XkcdExplainScrapedData | None:
        url = self.BASE_URL / f"wiki/index.php/{number}"

        soup = await self._get_soup(url)

        if soup.find("div", {"class": "noarticletext"}):
            return None

        try:
            explain_data = XkcdExplainScrapedData(
                number=number,
                explain_url=await self._extract_real_url(soup),
                tags=self._extract_tags(soup),
                raw_transcript=self._extract_transcript_html(soup),
            )
        except Exception as err:
            raise ScrapeError(url) from err
        else:
            return explain_data

    async def fetch_recently_updated_numbers(self, days: int = 1, limit: int = 500) -> list[int]:
        url = (
            self.BASE_URL
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

    async def _extract_real_url(self, soup: BeautifulSoup) -> URL:
        if tab := soup.find(id="ca-nstab-main"):
            if rel_url := tab.find("a").get("href"):
                return self.BASE_URL.joinpath(str(rel_url)[1:], encoded=True)
        raise ExtractError

    def _extract_tags(self, soup: BeautifulSoup) -> list[str]:
        tags = set()

        if li_tags := soup.find(id="mw-normal-catlinks").find_all("li"):
            tag_lower_set = set()
            for tag in [li.text for li in li_tags]:
                tag_lower = tag.lower()
                if not any(bad_word in tag_lower for bad_word in self.bad_tags):
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
