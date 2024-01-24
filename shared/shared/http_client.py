import asyncio
import json
import time
from contextlib import asynccontextmanager
from dataclasses import asdict, is_dataclass
from functools import partial
from typing import Any

from aiohttp import (
    AsyncResolver,
    ClientConnectorError,
    ClientOSError,
    ClientSession,
    ClientTimeout,
    ServerDisconnectedError,
    TCPConnector,
)
from aiohttp_retry import ExponentialRetry, RetryClient
from yarl import URL


class CustomJsonEncoder(json.JSONEncoder):
    def default(self, value):
        if is_dataclass(value):
            return asdict(value)
        elif isinstance(value, URL):
            return str(value)
        else:
            return super().default(value)


custom_json_dumps = partial(json.dumps, cls=CustomJsonEncoder)


class HttpClient:
    _CLIENTS_WITH_TS_CACHE: dict[str, tuple[ClientSession, float]] = {}

    def __init__(
        self,
        throttler: asyncio.Semaphore | None = asyncio.Semaphore(20),
    ):
        self._throttler = throttler
        self._close_sessions_task = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close_all_sessions()

    def _create_retry_client(self, session: ClientSession):
        return RetryClient(
            raise_for_status=True,
            retry_options=ExponentialRetry(
                attempts=5,
                start_timeout=3,
                factor=1.5,
                exceptions={
                    TimeoutError,
                    ClientConnectorError,
                    ServerDisconnectedError,
                    ClientOSError,
                },
            ),
            client_session=session,
        )

    @asynccontextmanager
    async def safe_get(
        self,
        url: URL,
    ):
        client = self.get_or_create_client(url)

        async with self._throttler, client.get(url) as response:
            yield response

    @asynccontextmanager
    async def safe_post(
        self,
        url: URL,
        params: dict[str, str] | None = None,
        data: Any = None,
        json: Any = None,
    ):
        client = self.get_or_create_client(url)

        async with client.post(
            url=url,
            params=params,
            data=data,
            json=json,
        ) as response:
            yield response

    def get_or_create_client(self, url: URL) -> RetryClient:
        host = url.host
        client_with_timestamp = self._CLIENTS_WITH_TS_CACHE.get(host)

        if client_with_timestamp:
            client, _ = client_with_timestamp
        else:
            client = self._create_retry_client(session=self._create_session(host))

        self._CLIENTS_WITH_TS_CACHE[host] = client, time.time()

        return client

    @staticmethod
    def _create_session(host: str, timeout: int = 20):
        connector = None
        if host != "localhost":
            connector = TCPConnector(
                resolver=AsyncResolver(nameservers=["8.8.8.8", "8.8.4.4"]),
                ttl_dns_cache=600,
                ssl=False,
            )

        return ClientSession(
            connector=connector,
            timeout=ClientTimeout(timeout),
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
