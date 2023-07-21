import json
from dataclasses import asdict, dataclass, is_dataclass
from functools import partial

from aiohttp import web


@dataclass
class SuccessJSONData:
    status: str = "success"
    data: dict = None


@dataclass
class SuccessJSONDataWithMeta:
    status: str = "success"
    meta: dict = None
    data: list[dict] = None


@dataclass
class ErrorJSONData:
    status: str = "error"
    detail: dict | list = None


class DataClassJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if is_dataclass(obj):
            return asdict(obj)
        return super().default(obj)


def json_response(*args, **kwargs):
    kwargs['dumps'] = partial(json.dumps, cls=DataClassJSONEncoder)
    return web.json_response(*args, **kwargs)
