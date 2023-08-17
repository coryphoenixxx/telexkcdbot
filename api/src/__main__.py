from aiohttp import web

from src.config import Config
from src.setup import setup_app


def run_app():
    config = Config()
    app = setup_app(config)
    web.run_app(app, port=config.api_port)


if __name__ == "__main__":
    run_app()
