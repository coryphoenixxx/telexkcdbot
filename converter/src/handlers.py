import os
from pathlib import Path
from tempfile import NamedTemporaryFile

import magic
from bottle import FileUpload, redirect, request, static_file

from src.app import app
from src.conversion import convert_to_webp
from src.helpers import CustomError, handle_response, json_success_response, read_image_to_file


@app.get('/')
def root_handler():
    redirect('/healthcheck')


@app.get('/healthcheck')
def hello_handler():
    return json_success_response()


@app.post('/convert')
@handle_response
def convert_handler():
    image: FileUpload = request.files.get('image')

    if not image:
        raise CustomError("Empty body!")

    if image.filename == 'empty':
        raise CustomError("No attached file!")

    tmp_dir = app.config.tmp_dir
    if not os.path.exists(tmp_dir):
        raise CustomError("Invalid temp directory!")

    with NamedTemporaryFile(dir=tmp_dir) as input_file, \
            NamedTemporaryFile(dir=tmp_dir) as output_file:

        image_file = read_image_to_file(image.file, input_file, app.config.max_size)

        extension = magic.from_file(filename=image_file.name, mime=True).split('/')[1]
        if extension not in app.config.supported_extensions.split(','):
            raise CustomError(f"Invalid image extension! Supported: {app.config.supported_extensions}.")

        quality_param = request.query.quality
        convert_to_webp(
            input_path=image_file.name,
            output_path=output_file.name,
            bin_dir=app.config.bin,
            extension=extension,
            quality=quality_param if quality_param else app.config.quality,
        )

        response = static_file(
            filename=Path(output_file.name).name,
            root=tmp_dir,
            mimetype='image/webp',
        )

        input_image_size, output_image_size = os.path.getsize(image_file.name), os.path.getsize(output_file.name)
        compression_ratio = round((input_image_size - output_image_size) * 100 / input_image_size, 2)
        response.set_header('x-compression-ratio', compression_ratio)
        response.set_header('x-input-filename', image.filename)

        return response
