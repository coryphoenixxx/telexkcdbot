import asyncio

from aiohttp import web
from loguru import logger


async def hello(request: web.Request) -> web.Response:
    print("GET")
    return web.Response(text="Hello, world!")


async def web_server_start() -> None:
    loop = asyncio.get_event_loop()
    app = web.Application()
    app.add_routes([web.get("/", handler=hello)])
    runner = web.AppRunner(app)
    await runner.setup()
    await loop.create_server(runner.server, "127.0.0.1", 8080)
    logger.info("Web Server started at http://127.0.0.1:8080")
