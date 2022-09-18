from aiohttp import web
from loguru import logger

from telexkcdbot.api.databases.comics_initial_fill import comics_initial_fill
from telexkcdbot.api.databases.database import db
from telexkcdbot.config import ADMIN_ID

router = web.RouteTableDef()


@router.get("/api")
async def api_handler(request: web.Request) -> web.Response:
    return web.json_response({"status": "OK"}, status=200)


@router.get("/api/comics/last_comic_id")
async def get_last_comic_id(request: web.Request) -> web.Response:
    last_comic_id = await db.comics.get_last_comic_id()
    return web.json_response({"last_comic_id": last_comic_id}, status=200)


async def init() -> web.Application:
    app = web.Application()
    app.add_routes(router)

    await db.create()
    await comics_initial_fill()
    await db.users.add_user(ADMIN_ID)

    logger.info("Web Server started at http://localhost:8080")

    return app


if __name__ == "__main__":
    web.run_app(init(), port=8080)
