import re
from functools import wraps
from json import JSONDecodeError

from aiohttp import web
from pydantic import BaseModel, Field, ValidationError, field_validator
from src import types
from src.types import OrderType
from src.utils.json_response import ErrorPayload, json_response


class LimitOffsetParamsMixin(BaseModel):
    limit: int | None = Field(gt=0, default=None)
    offset: int | None = Field(gt=0, default=None)


class ComicFieldsParamMixin(BaseModel):
    fields: str | None = None

    @field_validator('fields')
    def validate_fields(cls, fields: str | None):
        if fields:
            invalid_fields = set(fields.split(',')) - set(types.ComicDTO.valid_field_names)
            if invalid_fields:
                raise ValueError(
                    f"Invalid 'fields' query param. Must be one of: {', '.join(types.ComicDTO.valid_field_names)}")
        return fields


class ComicQueryParams(ComicFieldsParamMixin):
    language: types.LanguageCode | None = None


class ComicsQueryParams(LimitOffsetParamsMixin, ComicQueryParams):
    order: OrderType = OrderType.ESC


class ComicsSearchQueryParams(LimitOffsetParamsMixin, ComicQueryParams):
    q: str

    @field_validator('q')
    def validate_q(cls, v):
        v = re.sub(r'[^a-zA-Za-яA-Я0-9]', ' ', v).replace('\\', ' ')
        v = re.sub(r'\s+', ' ', v.strip()).replace(' ', ' & ')
        return v


def validate_queries(validator):
    def wrapper(handler):
        @wraps(handler)
        async def wrapped(request: web.Request):
            try:
                valid_query_params = validator(**request.rel_url.query)
            except ValidationError as err:
                errors = _clean_errors(err)

                return json_response(
                    data=ErrorPayload(detail=errors),
                    status=422,
                )
            return await handler(request, **valid_query_params.dict())

        return wrapped

    return wrapper


def validate_request_json(validator):
    def wrapper(handler):
        @wraps(handler)
        async def wrapped(request: web.Request):
            try:
                request_json = await request.json()
                valid_request_data = validator(**request_json)
            except ValidationError as err:
                errors = _clean_errors(err)

                return json_response(
                    data=ErrorPayload(detail=errors),
                    status=400,
                )
            except (JSONDecodeError, TypeError):
                return json_response(
                    data=ErrorPayload(
                        detail=[{'reason': "Invalid JSON format."}],
                    ),
                    status=400,
                )

            return await handler(request, valid_request_data)

        return wrapped

    return wrapper


def _clean_errors(error_obj: ValidationError) -> list:
    errors = []
    for err in error_obj.errors(include_url=False):
        errors.append({
            'loc': err.get('loc'),
            'msg': err.get('msg'),
        })
    return errors
