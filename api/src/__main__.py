from aiohttp import web

from src.api_config import API_PORT
from src.database.base import BaseDB
from src.views.routes import Router


async def setup(application: web.Application) -> web.Application:
    await BaseDB.init()
    Router.setup_routes(application)
    return application


app = web.Application()

if __name__ == "__main__":
    web.run_app(setup(app), port=API_PORT)
