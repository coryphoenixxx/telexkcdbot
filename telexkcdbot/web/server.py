import asyncio

from aiohttp import web
from loguru import logger


async def api_handler(request: web.Request) -> web.Response:
    return web.json_response({"status": "OK"}, status=200)


async def web_server_start() -> None:
    loop = asyncio.get_event_loop()
    app = web.Application()
    app.add_routes([web.get("/api", handler=api_handler)])

    runner = web.AppRunner(app)
    await runner.setup()
    await loop.create_server(runner.server, "127.0.0.1", 8080)
    logger.info("Web Server started at http://127.0.0.1:8080")
