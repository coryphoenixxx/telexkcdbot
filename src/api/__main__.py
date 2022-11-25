from aiohttp import web

from api.config import ADMIN_ID, API_PORT
from api.databases.database import db
from api.views import router


async def init() -> web.Application:
    app = web.Application()
    app.add_routes(router)

    await db.create()
    await db.users.add_user(ADMIN_ID)

    return app


if __name__ == "__main__":
    web.run_app(init(), port=API_PORT)
