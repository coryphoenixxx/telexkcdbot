from aiohttp import web
from src.utils.json_response import SuccessJSONData, json_response


class Router:
    routes = web.RouteTableDef()

    @classmethod
    def setup_routes(cls, app: web.Application):
        from src.views import comic_views, user_views  # noqa: F401

        app.router.add_routes(cls.routes)
        app.router.add_route('GET', '/api', cls.api_entrypoint)

    @classmethod
    async def api_entrypoint(cls, request: web.Request) -> web.Response:
        return json_response(
            data=SuccessJSONData(
                data=[r.path for r in cls.routes],
            ),
            status=200,
        )
