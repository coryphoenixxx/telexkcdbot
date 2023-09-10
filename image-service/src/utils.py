import json

from bottle import response


def json_success_response(status_code: int = 200, **kwargs):
    response.content_type, response.status = 'application/json', status_code
    return json.dumps({
        'status': "success",
        **kwargs,
    })


def json_error_response(reason: str | None = None, status_code: int = 400):
    response.content_type, response.status = 'application/json', status_code
    return json.dumps({
        'status': "error",
        'reason': reason,
    })
