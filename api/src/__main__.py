from aiohttp import web
from src.config import Config
from src.setup import setup


def run_app():
    config = Config()
    app = setup(config)
    web.run_app(app, port=config.api_port)


if __name__ == "__main__":
    run_app()
