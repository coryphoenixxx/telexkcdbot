from fastapi import APIRouter, Depends
from starlette import status

from src.app import DatabaseHolderDepStub
from src.app.comics.types import ComicID
from src.app.translations.service import TranslationService
from src.core.database import DatabaseHolder

from .dtos.response import TranslationResponseDTO
from .schemas.request import TranslationRequestSchema
from .schemas.response import TranslationResponseSchema
from .types import TranslationID

router = APIRouter(tags=["Translations"])


@router.post(
    "/comics/{comic_id}/translations",
    status_code=status.HTTP_201_CREATED,
)
async def add_translation(
    comic_id: ComicID,
    schema: TranslationRequestSchema,
    db_holder: DatabaseHolder = Depends(DatabaseHolderDepStub),
) -> TranslationResponseSchema:
    translation_req_dto = schema.to_dto()

    translation_resp_dto: TranslationResponseDTO = await TranslationService(
        db_holder=db_holder,
    ).create(comic_id, translation_req_dto)

    return translation_resp_dto.to_schema()


@router.put(
    "/comics/{comic_id}/translations/{translation_id}",
    status_code=status.HTTP_200_OK,
)
async def update_translation(
    comic_id: ComicID,
    translation_id: TranslationID,
    schema: TranslationRequestSchema,
    db_holder: DatabaseHolder = Depends(DatabaseHolderDepStub),
) -> TranslationResponseSchema:
    translation_req_dto = schema.to_dto()

    translation_resp_dto: TranslationResponseDTO = await TranslationService(
        db_holder=db_holder,
    ).update(comic_id, translation_id, translation_req_dto)

    return translation_resp_dto.to_schema()
