import os

import bottle
from webptools import grant_permission

from src.config import load_config


def create_app() -> bottle.Bottle:
    application: bottle.Bottle = bottle.default_app()

    application.config = load_config()

    bottle.BaseRequest.MEMFILE_MAX = application.config.max_size

    os.makedirs(application.config.tmp_dir, exist_ok=True)

    if application.config.bin['cwebp'] == 'cwebp' or application.config.bin['gif2webp'] == 'gif2webp':
        grant_permission()

    return application


app = create_app()
