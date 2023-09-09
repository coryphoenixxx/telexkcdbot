import decouple
from bottle import Bottle
from webptools import grant_permission


def load_config(app: Bottle):
    app.config.update({
        'port': decouple.config('PORT', default=8080, cast=int),
        'host': decouple.config('HOST', default='0.0.0.0'),
        'bin': {
            'cwebp': decouple.config('CWEBP_PATH', default='cwebp'),
            'gif2webp': decouple.config('GIF2WEBP_PATH', default='gif2webp'),
        },
        'default_q': decouple.config('DEFAULT_QUALITY', default=85),
        'dir': {
            'dst': decouple.config('DST_DIR', default='/static/images/'),
            'tmp': decouple.config('TMP_DIR', default='/tmp/'),
        },
        'debug': decouple.config('DEBUG', default=False, cast=bool),
    })

    if app.config['bin']['cwebp'] == 'cwebp' or app.config['bin']['gif2webp'] == 'gif2webp':
        grant_permission()
