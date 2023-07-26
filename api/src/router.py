from aiohttp import web
from src.utils.json_response import SuccessPayload, json_response


class Router(web.RouteTableDef):
    def setup_routes(self, app: web.Application):
        from src.views import comic_views, user_views  # noqa: F401

        app.router.add_routes(self)
        app.router.add_route('GET', '/api', self._api_base_endpoint)

    async def _api_base_endpoint(self, request: web.Request) -> web.Response:

        return json_response(
            data=SuccessPayload(
                data=[f"{r.method} {r.path}" for r in self],
            ),
            status=200,
        )


router = Router()
