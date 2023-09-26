import uvloop
from aiohttp import web

from src.config import Config
from src.setup import create_app

if __name__ == "__main__":
    config = Config()
    web.run_app(create_app(config), port=config.api.port, loop=uvloop.new_event_loop())
