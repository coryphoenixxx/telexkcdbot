import json
from dataclasses import asdict, dataclass, is_dataclass
from functools import partial
from typing import Any

from aiohttp import web
from pydantic import ValidationError


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
    detail: dict | list[dict] | ValidationError = None

    @staticmethod
    def _clean_errors(error_obj: ValidationError) -> list[dict]:
        errors = []
        for err in error_obj.errors(include_url=False):
            errors.append({
                'loc': err.get('loc'),
                'msg': err.get('msg'),
            })
        return errors

    def __post_init__(self):
        if type(self.detail) == ValidationError:
            self.detail = self._clean_errors(self.detail)


class DataClassJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if is_dataclass(obj):
            return asdict(obj)
        return super().default(obj)


def json_response(*args, **kwargs):
    kwargs['dumps'] = partial(json.dumps, cls=DataClassJSONEncoder)
    return web.json_response(*args, **kwargs)


def json_error_response(reason: str | None = None, detail: Any = None, code: int = 400):
    # TODO
    if reason:
        detail = {'reason': reason}
    return json_response(
        data=ErrorPayload(
            detail=detail,
        ),
        status=code,
    )
