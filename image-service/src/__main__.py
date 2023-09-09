import json
import os
from uuid import uuid4

import bjoern
import bottle
from bottle import get, post, request, response

from src.config import load_config
from src.conversion import convert


@get('/healthcheck')
def hello_handler():
    response.status = 200
    response.content_type = 'application/json'
    return json.dumps({'status': "ok"})


@post('/convert')
def convert_handler():
    comic_id = request.query.comic_id
    language = request.query.lang
    tmp_image = request.query.path

    if not comic_id or not language or not tmp_image:
        response_obj, status_code = {
            'status': "error",
            'reason': "Invalid query strings: path, lang or comic_id!",
        }, 400
    else:
        quality = request.query.get('q', app.config['default_q'])
        extension = request.query.get('ext', 'jpg')

        filename = f"{comic_id}-{language}_{uuid4().hex}.webp"

        dst_dir, tmp_dir = app.config['dir']['dst'], app.config['dir']['tmp']
        os.makedirs(dst_dir, exist_ok=True)
        os.makedirs(tmp_dir, exist_ok=True)

        status, err = convert(
            input_path=tmp_dir + tmp_image,
            output_path=dst_dir + filename,
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
                'image': filename,
            }, 201

    response.content_type = 'application/json'
    response.status = status_code
    return json.dumps(response_obj)


if __name__ == '__main__':
    app = bottle.default_app()

    load_config(app)

    bjoern.run(
        app,
        app.config['host'],
        app.config['port'],
    )
