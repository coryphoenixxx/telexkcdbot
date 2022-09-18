import aiohttp
from aiohttp import web
from loguru import logger

router = web.RouteTableDef()


@router.get("/")
async def api_handler(request: web.Request) -> web.Response:
    async with aiohttp.ClientSession() as session:
        async with session.get("http://localhost:8080/api/comics/last_comic_id") as resp:
            print(resp.status)
            print(await resp.text())


async def init() -> web.Application:
    app = web.Application()
    app.add_routes(router)

    logger.info("Web Client started at http://localhost:9090")

    return app


if __name__ == "__main__":
    web.run_app(init(), port=9090)
