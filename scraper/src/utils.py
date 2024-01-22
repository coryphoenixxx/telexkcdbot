import functools
import json
import time
from collections.abc import Callable
from dataclasses import asdict, is_dataclass
from functools import partial
from typing import Any

from yarl import URL


def ranges(start, end, size):
    for i in range(start, end, size):
        if i + size > end:
            yield i, end
            break
        yield i, i + size - 1


class CustomJsonEncoder(json.JSONEncoder):
    def default(self, value):
        if is_dataclass(value):
            return asdict(value)
        elif isinstance(value, URL):
            return str(value)
        else:
            return super().default(value)


custom_json_dumps = partial(json.dumps, cls=CustomJsonEncoder)


def async_timed():
    def wrapper(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapped(*args, **kwargs) -> Any:
            print(f"выполняется {func} с аргументами {args} {kwargs}")
            start = time.time()
            try:
                return await func(*args, **kwargs)
            finally:
                end = time.time()
                total = end - start
                print(f"{func} завершилась за {total:.4f} с")

        return wrapped

    return wrapper
