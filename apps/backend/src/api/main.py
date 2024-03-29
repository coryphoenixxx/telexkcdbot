import logging

import uvicorn
from uvicorn.workers import UvicornWorker


class CustomUvicornWorker(UvicornWorker):
    CONFIG_KWARGS = {  # noqa
        "loop": "uvloop",
        "http": "httptools",
        "lifespan": "on",
        "app": "api.app:app",
        "reload": True,
        "log_level": logging.DEBUG,
    }


if __name__ == "__main__":
    uvicorn.run(**CustomUvicornWorker.CONFIG_KWARGS)
