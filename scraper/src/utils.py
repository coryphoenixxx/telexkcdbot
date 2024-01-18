import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Any

from aiohttp import (
    AsyncResolver,
    ClientConnectorError,
    ClientResponse,
    ClientSession,
    ClientTimeout,
    TCPConnector,
)
from src.exceptions import UnexpectedStatusCodeError


def get_session(timeout: int = 10):
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
    throttler: asyncio.Semaphore,
    url: str,
    max_tries: int = 3,
    interval: float = 5,
) -> ClientResponse:
    for _ in range(max_tries):
        try:
            async with throttler, session.get(url=url) as response:
                status = response.status
                if status == 200:
                    yield response
                    break
                else:
                    logging.warning(f"{url} return invalid status code: {status}.")
                    raise UnexpectedStatusCodeError
        except (TimeoutError, UnexpectedStatusCodeError, ClientConnectorError):
            await asyncio.sleep(interval)
        except Exception:
            await session.close()
            raise
    else:
        logging.error(f"{url} is unavailable after {max_tries} attempts.")
