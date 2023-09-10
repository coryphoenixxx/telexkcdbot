import decouple
from bottle import ConfigDict


def load_config() -> ConfigDict:
    return ConfigDict(**{
        'port': decouple.config('PORT', default=8080, cast=int),
        'host': decouple.config('HOST', default='0.0.0.0'),
        'bin': {
            'cwebp': decouple.config('CWEBP_PATH', default='cwebp'),
            'gif2webp': decouple.config('GIF2WEBP_PATH', default='gif2webp'),
        },
        'output_dir': decouple.config('OUTPUT_DIR', default='/static/images/comics/'),
        'worker_num': decouple.config('WORKER_NUM', default=3, cast=int),
        'max_size': decouple.config('MAX_UPLOAD_SIZE', default=5 * 1024 * 1024, cast=int),
        'quality': decouple.config('DEFAULT_QUALITY', default=85, cast=int),
    })
