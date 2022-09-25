from dataclasses import asdict
from datetime import datetime

from aiohttp import web
from loguru import logger

from telexkcdbot.api.databases.comics_initial_fill import comics_initial_fill
from telexkcdbot.api.databases.database import db
from telexkcdbot.config import ADMIN_ID
from telexkcdbot.models import ComicData, ComicHeadlineInfo, TotalComicData

router = web.RouteTableDef()


@router.get("/api")
async def api_handler(request: web.Request) -> web.Response:
    return web.json_response({"status": "OK"}, status=200)


@router.post("/api/comics")
async def add_new_comic(request: web.Request) -> web.Response:
    comic_data: dict = await request.json()
    comic_data["public_date"] = datetime.strptime(comic_data["public_date"], "%Y-%m-%d").date()
    await db.comics.add_new_comic(TotalComicData(**comic_data))
    return web.json_response({"comic_id": comic_data["comic_id"]}, status=201)


@router.get("/api/comics/latest_id")
async def get_latest_comic_id(request: web.Request) -> web.Response:
    latest_id = await db.comics.get_latest_id()
    return web.json_response({"latest_id": latest_id}, status=200)


@router.get("/api/comics/comics_ids")
async def get_all_comics_ids(request: web.Request) -> web.Response:
    comics_ids = await db.comics.get_all_comics_ids()
    return web.json_response({"comics_ids": comics_ids}, status=200)


@router.get("/api/comics/ru_comics_ids")
async def get_all_ru_comics_ids(request: web.Request) -> web.Response:
    ru_comics_ids = await db.comics.get_all_ru_comics_ids()
    return web.json_response({"ru_comics_ids": ru_comics_ids}, status=200)


@router.get("/api/comics/{comic_id}")
async def get_comic_data_by_id(request: web.Request) -> web.Response:
    comic_id = int(request.match_info["comic_id"])
    comic_data: ComicData = await db.comics.get_comic_data_by_id(comic_id)
    comic_data.public_date = str(comic_data.public_date)
    return web.json_response(asdict(comic_data), status=200)


@router.get("/api/comics/headlines/")
async def get_comics_headlines_info_by_title(request: web.Request) -> web.Response:
    title = request.rel_url.query.get("title")
    ids = request.rel_url.query.get("ids")
    lang = request.rel_url.query.get("lang")

    if ids is None:
        headline_info: list[ComicHeadlineInfo] = await db.comics.get_comics_headlines_info_by_title(title, lang)
        headline_info = [asdict(x) for x in headline_info]

        return web.json_response(headline_info, status=200)
    else:
        ids = [int(x) for x in ids.split(",")]
        headline_info: list[ComicHeadlineInfo] = await db.comics.get_comics_headlines_info_by_ids(ids, lang)
        headline_info = [asdict(x) for x in headline_info]

        return web.json_response(headline_info, status=200)


@router.patch("/api/comics/spec_status/{comic_id}")
async def toggle_spec_status(request: web.Request) -> web.Response:
    comic_id = int(request.match_info["comic_id"])
    await db.comics.toggle_spec_status(comic_id)
    return web.json_response({"toggled": comic_id}, status=200)


@router.post("/api/users")
async def add_user(request: web.Request) -> web.Response:
    user_id: dict = (await request.json())["user_id"]
    await db.users.add_user(user_id=user_id)
    return web.json_response({"user_id": user_id}, status=201)


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
