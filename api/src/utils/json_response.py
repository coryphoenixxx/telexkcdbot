import json
from dataclasses import asdict, dataclass, is_dataclass
from functools import partial

from aiohttp import web


@dataclass
class SuccessPayload:
    status: str = "success"
    data: dict | list[dict] = None


@dataclass
class Meta:
    limit: int | None
    offset: int | None
    count: int
    total: int


@dataclass
class SuccessPayloadWithMeta:
    status: str = "success"
    meta: Meta = None
    data: list[dict] = None


@dataclass
class ErrorPayload:
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
