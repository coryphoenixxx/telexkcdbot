import uvloop
from aiohttp import web

from src.config import Config
from src.setup import create_app


def run_app():
    config = Config()
    app = create_app(config)
    web.run_app(app, port=config.api_port, loop=uvloop.new_event_loop())


if __name__ == "__main__":
    run_app()
