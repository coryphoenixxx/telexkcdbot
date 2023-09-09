import json
import os

import bjoern
import bottle
from bottle import get, post, request, response

from src.config import load_config
from src.conversion import convert


@get('/healthcheck')
def hello_handler():
    response.content_type, response.status = 'application/json', 200
    return json.dumps({'status': "ok"})


@post('/convert')
def convert_handler():
    input_image, output_image = request.query.input, request.query.output

    if not input_image or not output_image:
        response_obj, status_code = {
            'status': "error",
            'reason': "Invalid query strings: input_image or output_image!",
        }, 422
    else:
        quality = request.query.get('q', app.config['default_q'])
        extension = request.query.get('ext', 'jpg')

        status, err = convert(
            input_path=app.config['dir']['tmp'] + input_image,
            output_path=app.config['dir']['dst'] + output_image,
            bin_path=app.config['bin']['gif2webp'] if extension == 'gif' else app.config['bin']['cwebp'],
            q=quality,
        )

        if not status:
            response_obj, status_code = {
                'status': "error",
                'reason': err.strip(),
            }, 400
        else:
            response_obj, status_code = {
                'status': "success",
                'image': output_image,
            }, 201

    response.content_type, response.status = 'application/json', status_code
    return json.dumps(response_obj)


if __name__ == '__main__':
    app = bottle.default_app()

    load_config(app)

    os.makedirs(app.config['dir']['dst'], exist_ok=True)
    os.makedirs(app.config['dir']['tmp'], exist_ok=True)

    bjoern.run(
        app,
        app.config['host'],
        app.config['port'],
    )
