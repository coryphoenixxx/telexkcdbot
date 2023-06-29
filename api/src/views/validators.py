from functools import wraps

import jsonschema
from aiohttp import web
from jsonschema import ValidationError

from src.databases.models import Base
from src.utils.json_data import ErrorJSONData


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
                    if not value.lstrip('-').isdigit():
                        raise InvalidQueryError(param_name, value)
                    else:
                        valid_query_params[param_name] = int(value)

            fields_param: str = request.rel_url.query.get('fields')
            if fields_param:
                resource_ = request.rel_url.raw_parts[2]
                model = Base.get_model_by_tablename(resource_)

                invalid_fields = set(fields_param.split(',')) - set(model.valid_column_names)
                if invalid_fields:
                    raise InvalidQueryError(param='fields', value=', '.join(invalid_fields))
                else:
                    valid_query_params['fields'] = fields_param

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
            entity = await request.json()

            try:
                jsonschema.validate(instance=entity, schema=json_schema)
            except ValidationError as err:
                return web.json_response(
                    data=ErrorJSONData(message=f"Invalid json: {err.message}").to_dict(),
                    status=400
                )
            return await handler_func(request, entity)

        return wrapped

    return wrapper
