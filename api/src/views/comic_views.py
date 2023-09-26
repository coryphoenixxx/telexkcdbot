from uuid import uuid4

from aiohttp import web
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.helpers.exceptions import CustomError
from src.helpers.json_response import SuccessPayload, json_response
from src.repositories.comic_repository import ComicRepository
from src.router import router
from src.schemas import schemas
from src.services.comic_service import ComicService
from src.services.converter_service import ConverterService
from src.services.image_service import ImageReaderService


@router.post('/api/comics')
async def api_post_comic(
        request: web.Request,
        session_factory: async_sessionmaker[AsyncSession],
) -> web.Response:
    if request.content_type != 'multipart/form-data':
        raise CustomError("Invalid MIME type. Only multipart/form-data supported.")

    reader = await request.multipart()
    image_reader = ImageReaderService()
    comic_data, image_repo = None, None
    async for body_part in reader:
        if body_part.name == 'data':
            comic_data = schemas.ComicOriginRequestSchema(**(await body_part.json()))
        elif body_part.name == 'image':
            if not comic_data:
                raise CustomError("Data part first!")
            if not body_part.filename:
                raise CustomError("No attached file!")
            image_repo = await image_reader.read_image_from_body_part(
                stem=f"{comic_data.comic_id:04}_en_{uuid4().hex}",
                image_body_part=body_part,
            )
            break

    comic_dto = comic_data.to_dto()

    response_dto = await ComicService(
        comic_repo=ComicRepository(session=session_factory()),
        image_repo=image_repo,
    ).create_comic(comic_dto)

    await ConverterService(
        comic_repo=ComicRepository(session=session_factory()),
        image_repo=image_repo,
    ).create_conversion_task(comic_id=comic_data.comic_id, lang='en')

    return json_response(
        data=SuccessPayload(data=response_dto.to_dict()),
        status=200,
    )
