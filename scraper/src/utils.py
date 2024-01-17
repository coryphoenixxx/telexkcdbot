import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Any

from aiohttp import AsyncResolver, ClientResponse, ClientSession, ClientTimeout, TCPConnector


def get_session(timeout: int):
    connector = TCPConnector(
        resolver=AsyncResolver(nameservers=["8.8.8.8", "8.8.4.4"]),
        ttl_dns_cache=600,
        ssl=False,
    )
    return ClientSession(connector=connector, timeout=ClientTimeout(timeout))


def get_throttler(connections: int):
    return asyncio.Semaphore(connections)


def value_or_none(value: Any) -> Any | None:
    return value if value else None


@asynccontextmanager
async def retry_get(
    session: ClientSession,
    url: str,
    max_tries: int = 3,
    interval: float = 5,
) -> ClientResponse:
    for _ in range(max_tries):
        try:
            async with session.get(url=url) as response:
                yield response
                break
        except TimeoutError:
            await asyncio.sleep(interval)
        except Exception:
            await session.close()
            raise
    else:
        logging.error(f"{url} is unavailable after {max_tries} attempts!")
