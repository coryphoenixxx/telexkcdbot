import json
from dataclasses import asdict, dataclass, is_dataclass
from functools import partial

from aiohttp import web
from sqlalchemy import Row


@dataclass
class BaseJSONData:
    status: str = None
    message: str = None
    data: dict | list[dict] = None


@dataclass
class SuccessJSONData(BaseJSONData):
    status: str = "success"

    def __post_init__(self):
        if self.data:
            if isinstance(self.data, Row):
                self.data = dict(self.data._mapping)
            elif isinstance(self.data, list) and all(isinstance(el, Row) for el in self.data):
                self.data = [dict(row._mapping) for row in self.data]

    def __or__(self, other: dict):
        return self.__dict__ | other

    def __ror__(self, other: dict):
        return other | self.__dict__


@dataclass
class ErrorJSONData(BaseJSONData):
    status: str = "error"


class DataClassJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if is_dataclass(obj):
            return asdict(obj)
        return super().default(obj)


def json_response(*args, **kwargs):
    kwargs['dumps'] = partial(json.dumps, cls=DataClassJSONEncoder)
    return web.json_response(*args, **kwargs)
