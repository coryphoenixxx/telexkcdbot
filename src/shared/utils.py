import asyncio
import datetime as dt
import functools
import json
import time
from collections.abc import Callable
from contextlib import contextmanager
from dataclasses import asdict, is_dataclass
from functools import partial
from typing import Any

from pydantic import BaseModel
from yarl import URL


def cast_or_none(type_: type[Any], value: Any) -> type[Any] | None:
    if value:
        return type_(value)


def timeit(func: Callable):
    @contextmanager
    def wrapping_logic():
        start_ts = time.monotonic()
        yield
        duration = time.monotonic() - start_ts
        print(f"\n\nFunction {func.__name__} took {duration} seconds")  # noqa

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if not asyncio.iscoroutinefunction(func):
            with wrapping_logic():
                return func(*args, **kwargs)
        else:

            async def tmp():
                with wrapping_logic():
                    return await func(*args, **kwargs)

            return tmp()

    return wrapper


def ranges(start, end, size):
    for i in range(start, end, size):
        if i + size > end:
            yield i, end
            break
        yield i, i + size - 1


def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


class CustomJsonEncoder(json.JSONEncoder):
    def default(self, value):
        if is_dataclass(value):
            return asdict(value)
        elif isinstance(value, URL | dt.date):
            return str(value)
        elif isinstance(value, BaseModel):
            return value.model_dump()
        else:
            return super().default(value)


custom_json_dumps = partial(json.dumps, cls=CustomJsonEncoder)
