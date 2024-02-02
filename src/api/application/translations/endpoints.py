from fastapi import Depends
from faststream.nats.fastapi import NatsRouter
from starlette import status

from api.application.dependency_stubs import DatabaseHolderDepStub
from api.application.translations.service import TranslationService
from api.core.database import DatabaseHolder

from .schemas.request import TranslationRequestSchema
from .schemas.response import TranslationResponseSchema
from .types import TranslationID

router = NatsRouter(tags=["Translations"])


@router.post(
    "/translations",
    status_code=status.HTTP_201_CREATED,
)
async def add_translation(
    schema: TranslationRequestSchema,
    db_holder: DatabaseHolder = Depends(DatabaseHolderDepStub),
) -> TranslationResponseSchema:
    translation_resp_dto = await TranslationService(
        db_holder=db_holder,
    ).create(schema.to_dto())

    return TranslationResponseSchema.from_dto(dto=translation_resp_dto)


@router.put(
    "/translations/{translation_id}",
    status_code=status.HTTP_200_OK,
)
async def update_translation(
    translation_id: TranslationID,
    schema: TranslationRequestSchema,
    db_holder: DatabaseHolder = Depends(DatabaseHolderDepStub),
) -> TranslationResponseSchema:
    # need comic_id in schema?
    translation_resp_dto = await TranslationService(
        db_holder=db_holder,
    ).update(translation_id, schema.to_dto())

    return TranslationResponseSchema.from_dto(dto=translation_resp_dto)


@router.delete(
    "/translations/{translation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_translation(
    translation_id: TranslationID,
    db_holder: DatabaseHolder = Depends(DatabaseHolderDepStub),
):
    await TranslationService(db_holder=db_holder).delete(translation_id)
