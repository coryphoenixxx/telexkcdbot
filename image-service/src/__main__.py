import json
from uuid import uuid4

from bottle import get, post, request, response, run

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
    quality = request.query.quality

    tmp_path = f"../../tmp/{tmp_image}"
    output_folder = f"../../static/images/comics/{comic_id}/"
    output_path = f"{comic_id}-{language}_{uuid4()}.webp"

    status, err = convert(
        input_path=tmp_path,
        output_path=output_folder + output_path,
        quality=quality,
    )

    if not status:
        response_obj, status_code = {
            'status': "error",
            'reason': err.strip(),
        }, 400
    else:
        response_obj, status_code = {
            'status': "success",
            'path': output_path,
        }, 201

    response.content_type = 'application/json'
    response.status = status_code
    return json.dumps(response_obj)


if __name__ == '__main__':
    run(host='0.0.0.0', port=8080, debug=True, server='bjoern')
