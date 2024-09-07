import asyncio
import datetime as dt
import json
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from dataclasses import asdict, is_dataclass
from functools import partial
from types import TracebackType
from typing import Any

from aiohttp import (
    AsyncResolver,
    ClientResponse,
    ClientSession,
    ClientTimeout,
    ServerConnectionError,
    TCPConnector,
)
from aiohttp_retry import ExponentialRetry, RetryClient
from pydantic import BaseModel
from yarl import URL


class JsonEncoder(json.JSONEncoder):
    def default(self, value: Any) -> Any:
        if is_dataclass(value):
            return asdict(value)
        if isinstance(value, URL | dt.date):
            return str(value)
        if isinstance(value, BaseModel):
            return value.model_dump()

        return super().default(value)


class AsyncHttpClient:
    def __init__(
        self,
        max_conns: int = 25,
        timeout: int = 60,
        attempts: int = 5,
        start_timeout: float = 1,
        exceptions: tuple[type[Exception]] | None = (
            TimeoutError,
            ServerConnectionError,
            ConnectionError,
        ),
    ) -> None:
        self._throttler = asyncio.Semaphore(max_conns)
        self._timeout = timeout
        self._attempts = attempts
        self._start_timeout = start_timeout
        self._exceptions = exceptions
        self._clients_cache = {}

    async def __aenter__(self) -> "AsyncHttpClient":
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await self.close_all_sessions()

    @asynccontextmanager
    async def safe_get(
        self,
        url: URL,
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
    async def safe_request(
        self,
        method: str,
        url: URL,
        retry_statuses: tuple[int] | None,
        **kwargs,
    ) -> AsyncGenerator[ClientResponse, None]:
        client: RetryClient = self._get_retry_client(url, retry_statuses)

        async with self._throttler, client.request(method=method, url=url, **kwargs) as response:
            yield response

    def _get_retry_client(
        self,
        url: URL,
        retry_statuses: tuple[int] | None,
    ) -> RetryClient:
        if client := self._clients_cache.get((url.host, retry_statuses)):
            return client
        client = self._create_retry_client(retry_statuses)
        self._clients_cache[(url.host, retry_statuses)] = client
        return client

    def _create_retry_client(self, retry_statuses: tuple[int] | None) -> RetryClient:
        return RetryClient(
            raise_for_status=False,
            retry_options=ExponentialRetry(
                attempts=self._attempts,
                start_timeout=self._start_timeout,
                exceptions=self._exceptions,
                retry_all_server_errors=False,
                statuses=set(retry_statuses) if retry_statuses else None,
            ),
            client_session=self._create_session(),
        )

    def _create_session(self) -> ClientSession:
        return ClientSession(
            connector=TCPConnector(
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
                limit=100,
                limit_per_host=100,
            ),
            timeout=ClientTimeout(self._timeout),
            json_serialize=partial(json.dumps, cls=JsonEncoder),
        )

    async def close_all_sessions(self) -> None:
        for client in self._clients_cache.values():
            await client.close()
