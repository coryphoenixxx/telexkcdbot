from aiohttp import web

import src.views.comic_views as comics
from src.utils.json_response_dataclasses import SuccessJSONData


class Router:
    __app: web.Application = None
    __routes = [
        web.get('/api/comics/{comic_id:\d+}', comics.api_get_comic),
        web.get('/api/comics', comics.api_get_comics),
        web.post('/api/comics', comics.api_post_comics),
        web.get('/api/comics/search', comics.api_get_found_comics),
    ]

    @classmethod
    def setup_routes(cls, app: web.Application):
        cls.__app = app
        cls.__routes.append(web.get('/api', cls.api_entrypoint))
        cls.__app.add_routes(cls.__routes)

    @classmethod
    async def api_entrypoint(cls, request: web.Request) -> web.Response:
        for resource in cls.__app.router.resources():
            print(resource.get_info())

        return web.json_response(
            data=SuccessJSONData(message="API is available.").to_dict(),
            status=200
        )
