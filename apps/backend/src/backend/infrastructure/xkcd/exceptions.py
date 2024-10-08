from dataclasses import dataclass

from yarl import URL


@dataclass(slots=True)
class ExtractError(Exception): ...


@dataclass(slots=True)
class ScrapeError(Exception):
    url: URL

    @property
    def message(self) -> str:
        return f"Failed to scrape `{self.url}`."
