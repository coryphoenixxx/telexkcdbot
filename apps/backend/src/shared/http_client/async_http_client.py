import asyncio
import time
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from aiohttp import (
    AsyncResolver,
    ClientOSError,
    ClientResponse,
    ClientSession,
    ClientTimeout,
    InvalidURL,
    ServerConnectionError,
    TCPConnector,
)
from aiohttp_retry import ExponentialRetry, RetryClient
from yarl import URL

from shared.http_client.exceptions import HttpRequestError
from shared.utils import custom_json_dumps


class AsyncHttpClient:
    def __init__(
        self,
        max_conns: int = 25,
        timeout: int = 60,
        session_cache_ttl: int = 60,
        attempts: int = 5,
        start_timeout: float = 2.0,
        exceptions: tuple[type[Exception]] | None = (
            TimeoutError,
            ServerConnectionError,
            ConnectionError,
        ),
    ):
        self._throttler = asyncio.Semaphore(max_conns)
        self._timeout = timeout
        self._attempts = attempts
        self._start_timeout = start_timeout
        self._exceptions = set(exceptions)
        self._sessions_cache = {}
        self._sessions_cache_ttl = session_cache_ttl

        self._close_sessions_task = None

    async def __aenter__(self) -> "AsyncHttpClient":
        self._close_sessions_task = asyncio.create_task(self.close_sessions_regularly())
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close_all_sessions()

    @asynccontextmanager
    async def safe_get(
        self,
        url: URL | str,
        retry_statuses: tuple[int] | None = (429, 500, 503),
        **kwargs,
    ) -> AsyncGenerator[ClientResponse, None]:
        async with self.safe_request(
            method="GET",
            url=url,
            retry_statuses=retry_statuses,
            **kwargs,
        ) as response:
            yield response

    @asynccontextmanager
    async def safe_post(
        self,
        url: URL | str,
        retry_statuses: tuple[int] | None = (429, 503),
        **kwargs,
    ) -> AsyncGenerator[ClientResponse, None]:
        async with self.safe_request(
            method="POST",
            url=url,
            retry_statuses=retry_statuses,
            **kwargs,
        ) as response:
            yield response

    @asynccontextmanager
    async def safe_request(
        self,
        method: str,
        url: URL | str,
        retry_statuses: tuple[int] | None,
        **kwargs,
    ) -> AsyncGenerator[ClientResponse, None]:
        if isinstance(url, str):
            url = URL(url)
        if url.host is None:
            raise InvalidURL(url)

        client: RetryClient | ClientSession = await self._get_or_create_client(
            host=url.host,
            retry_statuses=retry_statuses,
        )

        fail_reason: str = "Unknown"

        async with self._throttler:
            for _ in range(3):
                try:
                    async with client.request(method=method, url=url, **kwargs) as response:
                        yield response
                        break
                except ClientOSError as err:
                    fail_reason = str(err.__cause__)
                    await asyncio.sleep(0.1)
                    continue
            else:
                raise HttpRequestError(method, str(url), fail_reason)

    async def _get_or_create_client(
        self,
        host: str,
        retry_statuses: tuple[int] | None,
    ) -> RetryClient | ClientSession:
        key = (host, retry_statuses)
        client_with_ts = self._sessions_cache.get(key)

        if client_with_ts:
            client, _ = client_with_ts
            self._sessions_cache[key] = client, time.time()
        else:
            session = self._create_session(host)

            if not retry_statuses:
                client = session
            else:
                client = self._create_retry_client(session, retry_statuses)

            self._sessions_cache[key] = client, time.time()

        return client

    def _create_retry_client(
        self,
        session: ClientSession,
        retry_statuses: tuple[int],
    ) -> RetryClient:
        return RetryClient(
            raise_for_status=False,
            retry_options=ExponentialRetry(
                attempts=self._attempts,
                start_timeout=self._start_timeout,
                exceptions=self._exceptions,
                retry_all_server_errors=False,
                statuses=set(retry_statuses),
            ),
            client_session=session,
        )

    def _create_session(self, host: str) -> ClientSession:
        if host == "localhost":
            connector = None
        else:
            connector = TCPConnector(
                resolver=AsyncResolver(nameservers={"8.8.8.8", "8.8.4.4", "9.9.9.9", "1.1.1.1"}),
                ttl_dns_cache=600,
                ssl=False,
                limit=500,
                limit_per_host=100,
            )

        return ClientSession(
            connector=connector,
            timeout=ClientTimeout(self._timeout),
            json_serialize=custom_json_dumps,
        )

    async def close_all_sessions(self) -> None:
        for client, _ in self._sessions_cache.values():
            await client.close()

    async def close_sessions_regularly(self) -> None:
        ttl = self._sessions_cache_ttl

        while True:
            await asyncio.sleep(ttl)

            candidates = []
            for key, (_, timestamp) in self._sessions_cache.items():
                if (time.time() - timestamp) > ttl:
                    candidates.append(key)

            for key in candidates:
                client, _ = self._sessions_cache.pop(key)
                await client.close()
