import asyncio
import time
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from dataclasses import dataclass

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
from shared.http_client.json_encoder import custom_json_dumps


@dataclass
class HostData:
    client: RetryClient
    session: ClientSession
    timestamp: float


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
        self._exceptions = exceptions
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
        url = self._check_url(url)

        client: RetryClient = await self._get_or_create_client(
            host=url.host,
            retry_statuses=retry_statuses,
        )

        fail_reason: str = "Unknown"

        async with self._throttler:
            for _ in range(3):
                try:
                    async with client.request(
                        method=method,
                        url=url,
                        **kwargs,
                    ) as response:
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
    ) -> RetryClient:
        if host_data := self._sessions_cache.get(host):
            host_data.timestamp = time.time()
            self._sessions_cache[host] = host_data
            client = host_data.client
        else:
            session = self._create_session(host)
            client = self._create_retry_client(
                session=session,
                retry_statuses=retry_statuses,
            )
            self._sessions_cache[host] = HostData(
                client=client,
                session=session,
                timestamp=time.time(),
            )

        return client

    def get_session_by_host(self, host: str) -> ClientSession | None:
        if host_data := self._sessions_cache.get(host):
            return host_data.session

    def _create_retry_client(
        self,
        session: ClientSession,
        retry_statuses: tuple[int] | None,
    ) -> RetryClient:
        return RetryClient(
            raise_for_status=False,
            retry_options=ExponentialRetry(
                attempts=self._attempts,
                start_timeout=self._start_timeout,
                exceptions=self._exceptions,
                retry_all_server_errors=False,
                statuses=set(retry_statuses) if retry_statuses else None,
            ),
            client_session=session,
        )

    def _create_session(self, host: str) -> ClientSession:
        if host in ("localhost", "127.0.0.1"):
            connector = None
        else:
            connector = TCPConnector(
                resolver=AsyncResolver(
                    nameservers={
                        "8.8.8.8",
                        "8.8.4.4",
                        "9.9.9.9",
                        "1.1.1.1",
                    },
                ),
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

    def _check_url(self, url: str | URL) -> URL:
        if isinstance(url, str):
            url = URL(url)
        if url.host is None:
            raise InvalidURL(url)
        return url

    async def close_all_sessions(self) -> None:
        for host_data in self._sessions_cache.values():
            await host_data.client.close()

    async def close_sessions_regularly(self) -> None:
        while True:
            await asyncio.sleep(self._sessions_cache_ttl)

            for host, data in self._sessions_cache.copy().items():
                if (time.time() - data.timestamp) > self._sessions_cache_ttl:
                    data = self._sessions_cache.pop(host, None)
                    if data.client:
                        await data.client.close()
