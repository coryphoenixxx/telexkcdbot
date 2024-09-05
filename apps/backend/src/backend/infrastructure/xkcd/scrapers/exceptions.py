from yarl import URL


class ScraperError(Exception):
    def __init__(self, url: URL | str) -> None:
        super().__init__()
        self._message = f"Failed to scrape `{url}`."

    @property
    def message(self) -> str:
        return self._message

    def __str__(self) -> str:
        return self.message
