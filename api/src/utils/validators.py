from functools import wraps
from json import JSONDecodeError

from aiohttp import web
from pydantic import ValidationError
from src.utils.json_response import ErrorPayload, json_response


def validate_request_json(validator):
    def wrapper(handler):
        @wraps(handler)
        async def wrapped(request: web.Request, session_factory):
            try:
                request_json = await request.json()
                valid_request_data = validator(**request_json)
            except ValidationError as err:
                errors = clean_errors(err)

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

            return await handler(request, session_factory, valid_request_data)

        return wrapped

    return wrapper


def clean_errors(error_obj: ValidationError) -> list:
    errors = []
    for err in error_obj.errors(include_url=False):
        errors.append({
            'loc': err.get('loc'),
            'msg': err.get('msg'),
        })
    return errors
