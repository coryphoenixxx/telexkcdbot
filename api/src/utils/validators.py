from functools import wraps

import jsonschema
from aiohttp import web
from jsonschema import ValidationError

from src.database.models import Base
from src.utils.json_response_dataclasses import ErrorJSONData


class InvalidQueryError(Exception):
    def __init__(self, param, value):
        self.message = f"Invalid query parameter: '{param}' (={value})."
        super().__init__(self.message)


def validate_queries(handler_func):
    @wraps(handler_func)
    async def wrapped(request: web.Request):
        try:
            valid_query_params = {}

            for param_name in ('user_id', 'limit', 'offset'):
                value = request.rel_url.query.get(param_name)
                if value:
                    if not value.isdigit():
                        raise InvalidQueryError(param_name, value)
                    valid_query_params[param_name] = int(value)
                else:
                    valid_query_params[param_name] = 0

            order = request.rel_url.query.get('order')

            if order and order not in ('esc', 'desc'):
                raise InvalidQueryError('order', order)
            else:
                valid_query_params['order'] = order

            fields: str = request.rel_url.query.get('fields')
            if fields:
                resource_ = request.rel_url.raw_parts[2]
                print(request.rel_url.raw_parts)
                model = Base.get_model_by_tablename(resource_)  # dirty

                invalid_fields = set(fields.split(',')) - set(model.valid_column_names)
                if invalid_fields:
                    raise InvalidQueryError(param='fields', value=', '.join(invalid_fields))
                else:
                    valid_query_params['fields'] = fields

        except InvalidQueryError as err:
            return web.json_response(
                data=ErrorJSONData(message=err.message).to_dict(),
                status=422
            )

        valid_query_params['q'] = request.rel_url.query.get('q')

        return await handler_func(request, valid_query_params)

    return wrapped


comic_json_schema = {
    "type": "object",
    "properties": {
        "comic_id": {"type": "integer"},
        "title": {"type": "string"},
        "image": {"type": "string"},
        "comment": {"type": "string"},
        "transcript": {"type": "string"},
        "rus_title": {"type": "string"},
        "rus_image": {"type": "string"},
        "rus_comment": {"type": "string"},
        "publication_date": {"type": "string"},
        "is_specific": {"type": "boolean"},
    },
    "required": ["comic_id", "title", "image", "comment", "transcript", "is_specific"]
}


def validate_json(json_schema):
    def wrapper(handler_func):
        @wraps(handler_func)
        async def wrapped(request: web.Request):
            json_ = await request.json()

            try:
                jsonschema.validate(instance=json_, schema=json_schema)
            except ValidationError as err:
                return web.json_response(
                    data=ErrorJSONData(message=f"Invalid json: {err.message}").to_dict(),
                    status=400
                )
            return await handler_func(request, json_)

        return wrapped

    return wrapper
