from yarl import URL


class AsyncHttpClientError(Exception): ...


class HttpRequestError(AsyncHttpClientError):
    def __init__(self, url: URL | str, reason: str, method: str = "GET") -> None:
        super().__init__()
        self._message = f"{method} request to `{url}` failed, reason: `{reason}`"
        self._reason = reason

    @property
    def message(self) -> str:
        return self._message

    @property
    def reason(self) -> str:
        return self._reason

    def __str__(self) -> str:
        return self.message
