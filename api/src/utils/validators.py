import re
from enum import Enum
from functools import wraps

from aiohttp import web
from pydantic import BaseModel, Field, ValidationError, field_validator
from src.database.models import Comic
from src.utils.json_response import ErrorJSONData, json_response


class OrderType(str, Enum):
    DESC = "desc"
    ESC = "esc"


class LimitOffsetParamsMixin(BaseModel):
    limit: int | None = Field(gt=0, default=0)
    offset: int | None = Field(gt=0, default=0)


class ComicFieldsParamMixin(BaseModel):
    fields: str | None = None

    @field_validator('fields')
    def validate_fields(cls, v):
        if v:
            invalid_fields = set(v.split(',')) - set(Comic.column_names)
            if invalid_fields:
                raise ValueError(f"Invalid 'fields' query param. Must be one of: {', '.join(Comic.column_names)}")
        return v


class ComicQueryParams(ComicFieldsParamMixin):
    ...


class ComicsQueryParams(LimitOffsetParamsMixin, ComicFieldsParamMixin):
    order: OrderType | None = OrderType.ESC


class ComicsSearchQueryParams(LimitOffsetParamsMixin, ComicFieldsParamMixin):
    q: str | None = None

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
                    data=ErrorJSONData(detail=errors),
                    status=422,
                )
            return await handler(request, **valid_query_params.dict())

        return wrapped

    return wrapper


class ComicJSONSchema(BaseModel):
    comic_id: int
    title: str
    image: str
    comment: str
    transcript: str | None
    rus_title: str | None
    rus_image: str | None
    rus_comment: str | None
    publication_date: str
    is_specific: bool


def validate_post_json(validator):
    def wrapper(handler):
        @wraps(handler)
        async def wrapped(request: web.Request):
            request_json = await request.json()

            try:
                validator(**request_json)
            except ValidationError as err:
                errors = _clean_errors(err)

                return json_response(
                    data=ErrorJSONData(detail=errors),
                    status=400,
                )
            return await handler(request, request_json)

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
