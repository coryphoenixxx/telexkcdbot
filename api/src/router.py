from aiohttp import web
from src.utils.json_response import SuccessJSONData, json_response


class Router(web.RouteTableDef):
    def setup_routes(self, app: web.Application):
        from src.views import comic_views, user_views  # noqa: F401

        app.router.add_routes(self)
        app.router.add_route('GET', '/api', self._api_base_entrypoint)

    async def _api_base_entrypoint(self, request: web.Request) -> web.Response:
        return json_response(
            data=SuccessJSONData(
                data=[r.path for r in self],
            ),
            status=200,
        )


router = Router()
