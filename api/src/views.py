from aiohttp import web
from datetime import datetime
from sqlalchemy import select

from src.databases.base import db_pool
from src.databases.models import Comic

router = web.RouteTableDef()

# valid_comics_fields = {field.name for field in dataclasses.fields(TotalComicData)}

cyrillic = "АаБбВвГгДдЕеЁёЖжЗзИиЙйКкЛлМмНнОоПпРрСсТтУуФфХхЦцЧчШшЩщЪъЫыЬьЭэЮюЯя"
punctuation = " -(),.:;!?#+*/"


def is_cyrillic(text: str) -> bool:
    return set(text).issubset(cyrillic + punctuation)


@router.get("/api")
async def api_handler(request: web.Request) -> web.Response:
    return web.json_response({"status": "OK"}, status=200)


# @router.get("/api/comics")
# async def get_comics(request: web.Request) -> web.Response:
#     # fields = request.rel_url.query.get("fields")
#     # comic_ids = request.rel_url.query.get("comic_ids")
#     # title = request.rel_url.query.get("title")
#     #
#     # if fields:
#     #     if not set(fields.replace(" ", "").split(",")).issubset(valid_comics_fields):
#     #         return web.json_response(data={"error": "Invalid fields!"}, status=400)
#     # else:
#     #     fields = ",".join(valid_comics_fields)
#     #
#     # query = f"SELECT {fields} FROM comics".replace("public_date", "public_date::char(10)")
#     #
#     # conditions = []
#     #
#     # if title:
#     #     lang_params = ("russian", "ru_title", "ru_comment") if is_cyrillic(title) else ("english", "title", "comment")
#     #
#     #     title = " & ".join(title.split(" "))
#     #
#     #     conditions.append(
#     #         f"to_tsvector('{lang_params[0]}', {lang_params[1]})"
#     #         f" || to_tsvector('{lang_params[0]}', {lang_params[2]})"
#     #         f" @@ to_tsquery('{lang_params[0]}', '{title}')"
#     #         ""
#     #     )
#     #
#     # if comic_ids:
#     #     conditions.append(f"comic_id IN ({comic_ids})")
#     #
#     # if conditions:
#     #     query += " WHERE " + " AND ".join(conditions)
#     #
#     # logger.info(query)
#     #
#     # result = await db.pool.fetch(query)
#     # data = [dict(r) for r in result]
#     return web.json_response(data=..., status=200)


@router.get("/api/comics/latest_comic_id/")
async def get_latest_comic_id(request: web.Request) -> web.Response:
    # query = """SELECT comic_id FROM comics
    #            ORDER BY comic_id DESC
    #            LIMIT 1;"""
    #
    # latest_id: int = await db.pool.fetchval(query)
    # data = {"latest_id": latest_id}
    return web.json_response(data=..., status=200)


# !!!!!!!!!!!!!!
@router.get("/api/comics/comics_ids")
async def get_comics_ids(request: web.Request) -> web.Response:
    # lang = request.rel_url.query.get("lang")
    #
    # query = "SELECT array_agg(comic_id) FROM comics"
    #
    # if lang == "ru":
    #     query += " WHERE has_ru_translation = TRUE"
    #
    # result = await db.pool.fetchval(query)
    #
    # comics_ids = tuple(result) if result else ()
    # data = {"comics_ids": comics_ids}

    async with db_pool() as session:
        async with session.begin():
            stmt = select(Comic.comic_id)
            result = (await session.execute(stmt)).scalars()
        await session.commit()

    result = tuple(result) if result else ()
    return web.json_response(data={"comics_ids": result}, status=200)


# !!!!!!!!!!!!!!
@router.post("/api/comics")
async def add_new_comic(request: web.Request) -> web.Response:
    comic_data: dict = await request.json()
    comic_data["public_date"] = datetime.strptime(comic_data["public_date"], "%Y-%m-%d").date()

    # Добавить проверку, что вставилось!

    async with db_pool() as session:
        async with session.begin():
            session.add(Comic(**comic_data))
        await session.commit()

    return web.json_response(data={"comic_id": comic_data["comic_id"]}, status=201)

# @router.patch("/api/comics/spec_status/{comic_id}")
# async def toggle_spec_status(request: web.Request) -> web.Response:
#     comic_id = int(request.match_info["comic_id"])
#     await db.comics.toggle_spec_status(comic_id)
#     return web.json_response({"toggled": comic_id}, status=200)
#
#
# @router.post("/api/users")
# async def add_user(request: web.Request) -> web.Response:
#     user_id = (await request.json())["user_id"]
#     await db.users.add_user(user_id)
#     return web.json_response({"user_id": user_id}, status=201)
#
#
# @router.delete("/api/users/{user_id}")
# async def delete_user(request: web.Request) -> web.Response:
#     user_id = int(request.match_info["user_id"])
#     await db.users.delete_user(user_id)
#     return web.json_response({"user_id": user_id}, status=201)
#
#
# @router.get("/api/users/user_lang/{user_id}")
# async def get_user_lang(request: web.Request) -> web.Response:
#     user_id = int(request.match_info["user_id"])
#     user_lang = await db.users.get_user_lang(user_id)
#     return web.json_response({"user_lang": user_lang}, status=201)
#
#
# @router.patch("/api/users/user_lang/{user_id}")
# async def set_user_lang(request: web.Request) -> web.Response:
#     user_id = int(request.match_info["user_id"])
#     user_lang = (await request.json())["user_lang"]
#     await db.users.set_user_lang(user_id, user_lang)
#     return web.json_response({"user_lang": user_lang}, status=201)
#
#
# @router.get("/api/users/last_comic_info/{user_id}")
# async def get_last_comic_info(request: web.Request) -> web.Response:
#     user_id = int(request.match_info["user_id"])
#     last_comic_info = await db.users.get_last_comic_info(user_id)
#     return web.json_response({"last_comic_info": last_comic_info}, status=201)
#
#
# @router.patch("/api/users/last_comic_info/{user_id}")
# async def update_last_comic_info(request: web.Request) -> web.Response:
#     user_id = int(request.match_info["user_id"])
#     new_comic_id = (await request.json())["new_comic_id"]
#     new_comic_lang = (await request.json())["new_comic_lang"]
#     await db.users.update_last_comic_info(user_id, new_comic_id, new_comic_lang)
#     return web.json_response({"updated": user_id}, status=201)
#
#
# @router.get("/api/users/users_ids")
# async def get_all_users_ids(request: web.Request) -> web.Response:
#     users_ids = await db.users.get_all_users_ids()
#     return web.json_response({"users_ids": users_ids}, status=201)
#
#
# @router.get("/api/users/only_ru_mode_status/{user_id}")
# async def get_only_ru_mode_status(request: web.Request) -> web.Response:
#     user_id = int(request.match_info["user_id"])
#     only_ru_mode_status = await db.users.get_only_ru_mode_status(user_id)
#     return web.json_response({"only_ru_mode_status": only_ru_mode_status}, status=201)
#
#
# @router.patch("/api/users/only_ru_mode_status/{user_id}")
# async def toggle_only_ru_mode_status(request: web.Request) -> web.Response:
#     user_id = int(request.match_info["user_id"])
#     await db.users.toggle_only_ru_mode_status(user_id)
#     return web.json_response({"toggled": user_id}, status=201)
#
#
# @router.get("/api/users/ban_status/{user_id}")
# async def get_ban_status(request: web.Request) -> web.Response:
#     user_id = int(request.match_info["user_id"])
#     ban_status = await db.users.get_ban_status(user_id)
#     return web.json_response({"ban_status": ban_status}, status=201)
#
#
# @router.patch("/api/users/ban_status/{user_id}")
# async def ban_user(request: web.Request) -> web.Response:
#     user_id = int(request.match_info["user_id"])
#     await db.users.ban_user(user_id)
#     return web.json_response({"banned": user_id}, status=201)
#
#
# @router.get("/api/users/lang_btn_status/{user_id}")
# async def get_lang_btn_status(request: web.Request) -> web.Response:
#     user_id = int(request.match_info["user_id"])
#     lang_btn_status = await db.users.get_lang_btn_status(user_id)
#     return web.json_response({"lang_btn_status": lang_btn_status}, status=201)
#
#
# @router.patch("/api/users/lang_btn_status/{user_id}")
# async def toggle_lang_btn_status(request: web.Request) -> web.Response:
#     user_id = int(request.match_info["user_id"])
#     await db.users.toggle_lang_btn_status(user_id)
#     return web.json_response({"toggled": user_id}, status=201)
#
#
# @router.patch("/api/users/last_action_date/{user_id}")
# async def update_last_action_date(request: web.Request) -> web.Response:
#     user_id = int(request.match_info["user_id"])
#     action_date = (await request.json())["action_date"]
#     action_date = datetime.strptime(action_date, "%Y-%m-%d").date()
#     await db.users.update_last_action_date(user_id, action_date)
#     return web.json_response({"updated": user_id}, status=201)
#
#
# @router.get("/api/users/user_menu_info/{user_id}")
# async def get_user_menu_info(request: web.Request) -> web.Response:
#     user_id = int(request.match_info["user_id"])
#     user_menu_info: MenuKeyboardInfo = await db.users.get_user_menu_info(user_id)
#     return web.json_response(asdict(user_menu_info), status=200)
#
#
# @router.get("/api/users/bookmarks/{user_id}")
# async def get_bookmarks(request: web.Request) -> web.Response:
#     user_id = int(request.match_info["user_id"])
#     bookmarks = await db.users.get_bookmarks(user_id)
#     return web.json_response({"bookmarks": bookmarks}, status=201)
#
#
# @router.patch("/api/users/bookmarks/{user_id}")
# async def update_bookmarks(request: web.Request) -> web.Response:
#     user_id = int(request.match_info["user_id"])
#     new_bookmarks = (await request.json())["new_bookmarks"]
#     await db.users.update_bookmarks(user_id, new_bookmarks)
#     return web.json_response({"updated": user_id}, status=201)
#
#
# @router.get("/api/users/notification_sound_status/{user_id}")
# async def get_notification_sound_status(request: web.Request) -> web.Response:
#     user_id = int(request.match_info["user_id"])
#     notification_sound_status = await db.users.get_notification_sound_status(user_id)
#     return web.json_response({"notification_sound_status": notification_sound_status}, status=201)
#
#
# @router.patch("/api/users/notification_sound_status/{user_id}")
# async def toggle_notification_sound_status(request: web.Request) -> web.Response:
#     user_id = int(request.match_info["user_id"])
#     await db.users.toggle_notification_sound_status(user_id)
#     return web.json_response({"toggled": user_id}, status=201)
#
#
# @router.get("/api/users/admin_users_info")
# async def get_admin_users_info(request: web.Request) -> web.Response:
#     admin_users_info: AdminUsersInfo = await db.users.get_admin_users_info()
#     return web.json_response(asdict(admin_users_info), status=200)
