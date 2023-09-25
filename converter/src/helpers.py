import json
import tempfile
from io import BufferedRandom

from bottle import response


def json_success_response(**kwargs):
    response.content_type, response.status = 'application/json', 200
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


def handle_response(handler):
    def inner():
        try:
            resp = handler()
        except ConversionError:
            return json_error_response(reason="Image conversion error!", status_code=422)
        except CustomError as err:
            return json_error_response(reason=err.message)
        status_code = resp.status_code
        if status_code != 200:
            return json_error_response(reason=resp.body, status_code=status_code)
        return resp

    return inner


class CustomError(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message


class ConversionError(CustomError):
    ...


def read_image_to_file(image_file: BufferedRandom, input_file: tempfile.TemporaryFile, max_size: int):
    size, chunk_size = 0, 1024*16
    while True:
        buf = image_file.read(chunk_size)
        if not buf:
            break
        size += len(buf)
        if size > max_size:
            raise CustomError(f"The allowed upload file size ({max_size / 1024 / 1024} MB) has been exceeded!")
        input_file.write(buf)
    input_file.seek(0)
    return input_file
