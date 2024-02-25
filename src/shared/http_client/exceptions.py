from yarl import URL


class AsyncHttpClientError(Exception): ...


class HttpRequestError(AsyncHttpClientError):
    def __init__(self, method: str, url: URL | str, reason: str):
        super().__init__()
        self._message = f"{method} request to `{url}` failed, reason: `{reason}`"

    def __str__(self):
        return self._message
