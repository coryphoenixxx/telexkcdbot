from enum import Enum
from functools import wraps

from aiohttp import web
from pydantic import BaseModel, Field, ValidationError, field_validator
from src.database.models import Comic
from src.utils.json_response import ErrorJSONData, json_response


class OrderType(str, Enum):
    desc = "desc"
    esc = "esc"


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
    user_id: int | None = Field(gt=0, default=None)


class ComicsQueryParams(LimitOffsetParamsMixin, ComicFieldsParamMixin):
    order: OrderType | None = OrderType.esc


class ComicsSearchQueryParams(LimitOffsetParamsMixin, ComicFieldsParamMixin):
    q: str | None = None


def validate_queries(validator):
    def wrapper(handler):
        @wraps(handler)
        async def wrapped(request: web.Request):
            try:
                valid_query_params = validator(**request.rel_url.query)
            except ValidationError as err:
                return json_response(
                    data=ErrorJSONData(errors=err.json()),
                    status=422,
                )
            return await handler(request, valid_query_params.dict())

        return wrapped

    return wrapper


class ComicJSONSchema(BaseModel):
    comic_id: int
    title: str
    image: str
    comment: str
    transcript: str
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
                return json_response(
                    data=ErrorJSONData(errors=err.json()),
                    status=400,
                )
            return await handler(request, request_json)

        return wrapped

    return wrapper
