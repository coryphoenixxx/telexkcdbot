import os

import bottle
from webptools import grant_permission

from src.config import load_config


def create_app() -> bottle.Bottle:
    app: bottle.Bottle = bottle.default_app()

    app.config(**load_config())

    bottle.BaseRequest.MEMFILE_MAX = app.config.max_size

    os.makedirs(app.config.output_dir, exist_ok=True)
    os.makedirs('tmp', exist_ok=True)

    if app.config.bin['cwebp'] == 'cwebp' or app.config.bin['gif2webp'] == 'gif2webp':
        grant_permission()

    return app


app = create_app()
