from aiohttp import web


from src.api_config import API_PORT

from src.databases.base import engine
from src.views.comics import router
from src.databases.models import Base


async def init() -> web.Application:
    app = web.Application()
    app.add_routes(router)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    await engine.dispose()

    return app


if __name__ == "__main__":
    web.run_app(init(), port=API_PORT)
