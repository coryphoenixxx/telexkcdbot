import asyncio
import functools
import logging
from collections.abc import Callable, Coroutine, Sequence
from typing import Any


def cast_or_none(type_: type[Any], value: Any) -> type[Any] | None:
    if value:
        return type_(value)


def filter_keys(obj: dict, keys: Sequence[str], parent: dict | None = None):
    """
    Recursively delete keys from dict that are not passed in 'keys' parameter
    and after delete empty dicts.
    """
    if isinstance(obj, dict) and keys:
        for k, v in obj.copy().items():
            if k not in keys and not isinstance(v, dict):
                del obj[k]
            else:
                filter_keys(v, keys, obj)
        if obj == {} and parent is not None:
            for pk, pv in parent.copy().items():
                if pv == {}:
                    del parent[pk]
    return obj


def background_task_exception_handler(task: asyncio.Task) -> None:
    try:
        task.result()
    except asyncio.CancelledError:
        pass
    except Exception:
        logging.exception("Exception raised by task = %r", task.get_name())


def handle_task_exception(func: Callable) -> Callable:
    @functools.wraps(func)
    async def wrapper(*args, **kwargs) -> Any:
        asyncio.current_task().add_done_callback(background_task_exception_handler)
        return await func(*args, **kwargs)

    return wrapper


@handle_task_exception
async def run_every(
    seconds: float,
    func: Callable[..., Coroutine[Any, Any, Any]],
    *args,
    **kwargs,
):
    while True:
        await func(*args, **kwargs)
        await asyncio.sleep(seconds)
