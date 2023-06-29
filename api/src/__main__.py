from aiohttp import web

from src.api_config import API_PORT
from src.databases.base import BaseDB

from src.views.comics import router


async def init() -> web.Application:
    app = web.Application()
    app.add_routes(router)

    await BaseDB.init()

    return app


if __name__ == "__main__":
    web.run_app(init(), port=API_PORT)
