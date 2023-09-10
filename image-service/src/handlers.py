from tempfile import NamedTemporaryFile

from bottle import request

from src.app import app
from src.conversion import convert_to_webp
from src.utils import json_error_response, json_success_response


@app.get('/healthcheck')
def hello_handler():
    return json_success_response()


@app.post('/convert')
def convert_handler():
    output_image_filename = request.query.output

    if not output_image_filename:
        return json_error_response("Output query parameter is unfilled!", 422)

    content_type = request.content_type
    if not content_type:
        return json_error_response("Empty body!")
    else:
        extension = content_type.split('/')[1]

    supported_image_extensions = ('gif', 'png', 'jpeg', 'webp')
    if extension not in supported_image_extensions:
        return json_error_response(
            f"Invalid image extension! Must be one of: {', '.join(supported_image_extensions)}.", 415,
        )

    try:
        binary = request.body.getbuffer()
    except AttributeError:
        return json_error_response(f"Request image too large! Max size is {app.config.max_size}.", 413)

    with NamedTemporaryFile(dir='tmp') as temp_file:
        temp_file.write(binary)

        status, err = convert_to_webp(
            input_path=temp_file.name,
            output_path=app.config.output_dir + output_image_filename,
            bin_dir=app.config.bin,
            extension=extension,
            quality=app.config.quality,
        )

    if not status:
        return json_error_response(err.strip(), 400)
    else:
        return json_success_response(201, result=output_image_filename)
