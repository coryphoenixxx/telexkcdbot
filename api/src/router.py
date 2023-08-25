from aiohttp import web
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.helpers.json_response import SuccessPayload, json_response


class Router(web.RouteTableDef):
    def setup_routes(self, app: web.Application):
        from src.views import comic_views  # noqa: F401

        app.router.add_route('GET', '/api', self._api_base_endpoint)
        app.router.add_routes(self)

    async def _api_base_endpoint(self, _: web.Request, __: async_sessionmaker[AsyncSession]) -> web.Response:
        return json_response(
            data=SuccessPayload(
                data=[f"{r.method} {r.path}" for r in self],
            ),
            status=200,
        )


router = Router()
