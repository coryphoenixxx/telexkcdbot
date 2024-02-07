import asyncio
import time
from contextlib import asynccontextmanager
from typing import Any

from aiohttp import (
    AsyncResolver,
    ClientOSError,
    ClientSession,
    ClientTimeout,
    ServerDisconnectedError,
    TCPConnector,
)
from aiohttp_retry import ExponentialRetry, RetryClient
from yarl import URL

from shared.utils import custom_json_dumps


class HttpClient:
    _CLIENTS_WITH_TS_CACHE: dict[str, tuple[ClientSession, float]] = {}  # noqa

    def __init__(self, max_conns: int = 20, timeout: int = 20):
        self._throttler = asyncio.Semaphore(max_conns)
        self._close_sessions_task = None
        self._timeout = timeout

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close_all_sessions()

    @asynccontextmanager
    async def get(self, url):
        async with self._create_session() as session, session.get(url) as response:
            yield response

    @asynccontextmanager
    async def safe_get(
        self,
        url: URL | str,
        statuses: tuple[int] = (429, 500, 503),
    ):
        client = self._get_or_create_client(url, statuses)

        async with self._throttler, client.get(url) as response:
            yield response

    @asynccontextmanager
    async def safe_post(
        self,
        url: URL,
        params: dict[str, str] | None = None,
        data: Any = None,
        json: Any = None,
        statuses: tuple[int] = (429, 503),
    ):
        client = self._get_or_create_client(url, statuses)

        async with client.post(
            url=url,
            params=params,
            data=data,
            json=json,
        ) as response:
            yield response

    @staticmethod
    def _create_retry_client(session: ClientSession, statuses: tuple[int]):
        return RetryClient(
            raise_for_status=False,
            retry_options=ExponentialRetry(
                attempts=5,
                start_timeout=3,
                factor=1.5,
                exceptions={
                    TimeoutError,
                    ServerDisconnectedError,
                    ClientOSError,
                },
                retry_all_server_errors=False,
                statuses=set(statuses),
            ),
            client_session=session,
        )

    def _get_or_create_client(self, url: URL, statuses: tuple[int]) -> RetryClient:
        host = url.host
        client_with_timestamp = self._CLIENTS_WITH_TS_CACHE.get(host)

        if client_with_timestamp:
            client, _ = client_with_timestamp
        else:
            client = self._create_retry_client(
                session=self._create_session(host), statuses=statuses
            )

        self._CLIENTS_WITH_TS_CACHE[host] = client, time.time()

        return client

    def _create_session(self, host: str = "localhost"):
        connector = None
        if host != "localhost":
            connector = TCPConnector(
                resolver=AsyncResolver(nameservers=["8.8.8.8", "8.8.4.4"]),
                ttl_dns_cache=600,
                ssl=False,
            )

        return ClientSession(
            connector=connector,
            timeout=ClientTimeout(self._timeout),
            json_serialize=custom_json_dumps,
        )

    async def close_all_sessions(self):
        for _, (client, _) in self._CLIENTS_WITH_TS_CACHE.items():
            await client.close()

    async def close_unused_sessions_periodically(self, secs: int = 60):
        async def task(secs: int):
            while True:
                await asyncio.sleep(secs)

                hosts = []
                for host, (_, timestamp) in self._CLIENTS_WITH_TS_CACHE.items():
                    if (time.time() - timestamp) > secs:
                        hosts.append(host)

                for host in hosts:
                    client, _ = self._CLIENTS_WITH_TS_CACHE.pop(host)
                    await client.close()

        self._close_sessions_task = asyncio.create_task(task(secs))
