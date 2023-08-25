from json import JSONDecodeError

from aiohttp import MultipartReader, hdrs, web
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.database.exceptions import AlreadyExistsError, NotFoundError, SameTextInfoError
from src.database.repositories import ComicsRepo
from src.dtos import ImageObjDto
from src.helpers.json_response import SuccessPayload, json_error_response, json_response
from src.router import router
from src.schemas import schemas
from src.schemas.queries import ComicQueryParams
from src.services.comics_service import ComicsService


@router.get('/api/comics/{comic_id:\\d+}')
async def api_get_comic_by_id(
        request: web.Request,
        session_factory: async_sessionmaker[AsyncSession],
) -> web.Response:
    comic_id = int(request.match_info['comic_id'])

    try:
        params = ComicQueryParams(**request.rel_url.query)
    except ValidationError as err:
        return json_error_response(detail=err, code=422)

    try:
        comic_dto = await ComicsService(ComicsRepo(session_factory())).get_comic_by_id(comic_id)
    except NotFoundError:
        return json_error_response(reason=f"Comic {comic_id} doesn't exists.", code=404)

    response_data = comic_dto.filter(params.languages, params.fields)

    return json_response(
        data=SuccessPayload(data=response_data),
        status=200,
    )


# @router.get('/api/comics')
# @validate_queries(validator=ComicsQueryParams)
# async def api_get_comic_list(
#         _: web.Request,
#         session_factory: async_sessionmaker[AsyncSession],
#         language: types.LanguageCode,
#         fields: str | None,
#         limit: int | None,
#         offset: int | None,
#         order: types.OrderType | None,
# ) -> web.Response:
#     comic_repo = ComicsRepository(session_factory)
#     comic_dto_list, total = await comic_repo.get_list(limit, offset, order)
#
#     response_data = [comic_dto.filter(language, fields) for comic_dto in comic_dto_list]
#
#     return json_response(
#         data=SuccessPayloadWithMeta(
#             meta=Meta(
#                 limit=limit,
#                 offset=offset,
#                 count=len(comic_dto_list),
#                 total=total,
#             ),
#             data=response_data),
#         status=200,
#     )
#
#
# @router.get('/api/comics/search')
# @validate_queries(validator=ComicsSearchQueryParams)
# async def api_search_comics(
#         _: web.Request,
#         session_factory: async_sessionmaker[AsyncSession],
#         language: types.LanguageCode,
#         fields: str | None,
#         limit: int | None,
#         offset: int | None,
#         q: str,
# ) -> web.Response:
#     comic_repo = ComicsRepository(session_factory)
#     comic_dto_list, total = await comic_repo.search(q, limit, offset)
#
#     response_data = [comic_dto.filter(language, fields) for comic_dto in comic_dto_list]
#
#     return json_response(
#         data=SuccessPayloadWithMeta(
#             meta=Meta(
#                 limit=limit,
#                 offset=offset,
#                 count=len(comic_dto_list),
#                 total=total,
#             ),
#             data=response_data),
#         status=200,
#     )


@router.post('/api/comics')
async def api_post_comic(
        request: web.Request,
        session_factory: async_sessionmaker[AsyncSession],
) -> web.Response:
    if request.content_type != 'multipart/form-data':
        return json_error_response(reason="Invalid MIME type. Only multipart/form-data supported.")

    reader: MultipartReader = await request.multipart()

    comic_json_data, images_data = None, {}

    async for field in reader:
        if field.name == 'data':
            try:
                comic_json_data = schemas.RequestComicSchema(**(await field.json()))
            except ValidationError as err:
                return json_error_response(detail=err, code=422)
            except (JSONDecodeError, TypeError):
                return json_error_response(reason="Invalid JSON format.")

        elif field.name.endswith('_image'):
            lang_code = field.name.split('_')[0]
            try:
                lang_code = schemas.LanguageCode(lang_code)
            except ValueError:
                return json_error_response(reason="Invalid lang.")

            supported_image_extensions = ('gif', 'png', 'jpeg', 'webp')
            content_type = field.headers[hdrs.CONTENT_TYPE]

            if content_type.split('/')[1] not in supported_image_extensions:
                return json_error_response(
                    reason=f"Invalid image extension. Must be one of: {', '.join(supported_image_extensions)}",
                )

            images_data[lang_code] = await field.read()

        else:
            ...

    if not comic_json_data:
        return json_error_response(reason="Must be 'data' field with comic data json!")

    comic_dto = comic_json_data.to_dto()

    images_objs = []
    for lang, imgb in images_data.items():
        img_obj = ImageObjDto(
            comic_id=comic_json_data.comic_id,
            language=lang,
            image_binary=imgb,
        )
        images_objs.append(img_obj)

    try:
        comic_dto = await ComicsService(ComicsRepo(session_factory())).create_comic(comic_dto, images_objs)
    except AlreadyExistsError:
        return json_error_response(detail=f"Comic {comic_dto.comic_id} already exists!", code=409)
    except SameTextInfoError:
        return json_error_response(
            detail="A comic with the same title, transcript or comment already exists.",
            code=409,
        )

    return json_response(
        data=SuccessPayload(data=comic_dto.to_dict()),
        status=201,
    )

#
#
# @router.put('/api/comics/{comic_id:\\d+}')
# @validate_request_json(validator=types.PutComic)
# async def api_put_comic(
#         request: web.Request,
#         session_factory: async_sessionmaker[AsyncSession],
#         new_comic_data: types.PutComic,
# ) -> web.Response:
#     comic_id = int(request.match_info['comic_id'])
#
#     comic_repo = ComicsRepository(session_factory)
#
#     try:
#         comic_data = await comic_repo.update(comic_id, new_comic_data)
#     except IntegrityError:
#         return json_response(
#             data=ErrorPayload(detail=[{'reason': "A comic with the same id, title and comment already exists."}]),
#             status=409,
#         )
#
#     if not comic_data:
#         return json_response(
#             data=ErrorPayload(detail=[{"reason": f"Comic {comic_id} doesn't exists."}]),
#             status=404,
#         )
#
#     return json_response(
#         data=SuccessPayload(data=comic_data.model_dump()),
#         status=200,
#     )
#
#
# @router.delete('/api/comics/{comic_id:\\d+}')
# async def api_delete_comic(request: web.Request, session_factory: async_sessionmaker[AsyncSession] ):
#     comic_id = int(request.match_info['comic_id'])
#
#     comic_repo = ComicsRepository(session_factory)
#     del_comic_id = await comic_repo.delete(comic_id)
#
#     if not del_comic_id:
#         return json_response(
#             data=ErrorPayload(detail=[{"reason": f"Comic {comic_id} doesn't exists."}]),
#             status=404,
#         )
#
#     return json_response(status=204)
