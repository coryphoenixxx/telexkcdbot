import datetime as dt
import json
from dataclasses import asdict, is_dataclass
from functools import partial

from pydantic import BaseModel
from yarl import URL


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
