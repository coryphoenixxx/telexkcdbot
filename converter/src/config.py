from functools import cache

import decouple
from bottle import ConfigDict


@cache
def load_config() -> ConfigDict:
    return ConfigDict(**{
        'port': decouple.config('PORT', default=8080, cast=int),
        'host': decouple.config('HOST', default='0.0.0.0'),
        'bin': {
            'cwebp': decouple.config('CWEBP_PATH', cast=lambda v: v if v else 'cwebp'),
            'gif2webp': decouple.config('GIF2WEBP_PATH', cast=lambda v: v if v else 'gif2webp'),
        },
        'tmp_dir': decouple.config('TMP_DIR'),
        'worker_num': decouple.config('WORKER_NUM', default=3, cast=int),
        'max_size': eval(decouple.config('MAX_UPLOAD_SIZE', default=2 * 1024 * 1024)),
        'quality': decouple.config('DEFAULT_QUALITY', default=85, cast=int),
        'supported_extensions': decouple.config('SUPPORTED_EXTENSIONS'),
    })
