import datetime as dt
import json
from dataclasses import asdict, is_dataclass
from functools import partial
from typing import Any

from pydantic import BaseModel
from yarl import URL


class CustomJsonEncoder(json.JSONEncoder):
    def default(self, value: Any) -> Any:
        if is_dataclass(value):
            return asdict(value)
        if isinstance(value, URL | dt.date):
            return str(value)
        if isinstance(value, BaseModel):
            return value.model_dump()

        return super().default(value)


custom_json_dumps = partial(json.dumps, cls=CustomJsonEncoder)
