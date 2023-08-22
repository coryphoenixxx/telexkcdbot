import re

from pydantic import BaseModel, Field, field_validator
from src.schemas import mytypes
from src.schemas.mytypes import LanguageCode, OrderType


class LimitOffsetParamsMixin(BaseModel):
    limit: int | None = Field(gt=0, default=None)
    offset: int | None = Field(gt=0, default=None)


class ComicFieldsParamMixin(BaseModel):
    fields: str | None = None

    @field_validator('fields')
    def validate_fields(cls, fields: str | None):
        if fields:
            invalid_fields = set(fields.split(',')) - set(mytypes.ComicSchema.valid_field_names)
            if invalid_fields:
                raise ValueError(
                    f"Invalid 'fields' query param. Must be one of: {', '.join(mytypes.ComicSchema.valid_field_names)}")
        return fields


class ComicQueryParams(ComicFieldsParamMixin):
    languages: str | None = None

    @field_validator('languages')
    def validate_languages(cls, languages: str | None):
        if languages:
            try:
                [LanguageCode(lang) for lang in languages.split(',')]
            except ValueError as err:
                raise ValueError(
                    f"Invalid 'languages' query param. Must be on of {LanguageCode.as_str()}",
                ) from err
        return languages


class ComicsQueryParams(LimitOffsetParamsMixin, ComicQueryParams):
    order: OrderType = OrderType.ESC


class ComicsSearchQueryParams(LimitOffsetParamsMixin, ComicQueryParams):
    q: str

    @field_validator('q')
    def validate_q(cls, v):
        v = re.sub(r'[^a-zA-Za-яA-Я0-9]', ' ', v).replace('\\', ' ')
        v = re.sub(r'\s+', ' ', v.strip()).replace(' ', ' & ')
        return v
