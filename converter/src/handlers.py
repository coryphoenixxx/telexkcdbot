import os
from tempfile import NamedTemporaryFile
from uuid import uuid4

from bottle import FileUpload, request, static_file

from src.app import app
from src.conversion import convert_to_webp
from src.utils import json_error_response, json_success_response


@app.get('/healthcheck')
def hello_handler():
    return json_success_response()


@app.post('/convert')
def convert_handler():
    image: FileUpload = request.files.get('image')
    quality_param = request.query.quality
    format_param = request.query.format

    if not image:
        return json_error_response("Empty body!")

    if image.filename == 'empty':
        return json_error_response("No attached file!")

    extension = image.content_type.split('/')[1]
    if extension not in app.config.supported_extensions:
        return json_error_response(
            f"Invalid image extension! Must be one of: {', '.join(app.config.supported_extensions)}.", 415,
        )

    with NamedTemporaryFile(dir=app.config.tmp_dir) as temp_file:
        image.save(temp_file)

        input_image_size = temp_file.tell()
        output_filename = f"{uuid4().hex}.webp"
        output_path = app.config.static_dir + output_filename

        status, error = convert_to_webp(
            input_path=temp_file.name,
            output_path=output_path,
            bin_dir=app.config.bin,
            extension=extension,
            quality=quality_param if quality_param else app.config.quality,
        )

    if not status:
        return json_error_response(error.strip(), 422)
    elif format_param == 'image':
        return static_file(
            filename=output_filename,
            root=app.config.static_dir,
            mimetype='image/webp',
        )
    else:
        output_image_size = os.path.getsize(output_path)
        compression_ratio = round((input_image_size - output_image_size) * 100 / input_image_size, 2)
        return json_success_response(
            input_image=image.filename,
            output_image=output_filename,
            compression_ratio=f"{compression_ratio}%",
        )
