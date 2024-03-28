import logging

from uvicorn.workers import UvicornWorker


class CustomUvicornWorker(UvicornWorker):
    CONFIG_KWARGS = {  # noqa
        "loop": "uvloop",
        "http": "httptools",
        "lifespan": "on",
    }


if __name__ == "__main__":
    import uvicorn

    from api.infrastructure.settings import load_settings

    settings = load_settings()

    uvicorn.run(
        **CustomUvicornWorker.CONFIG_KWARGS,
        app="api.app:app",
        reload=True,
        log_level=logging.ERROR,
    )
