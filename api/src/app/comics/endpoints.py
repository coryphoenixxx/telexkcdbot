from fastapi import APIRouter, Depends
from starlette import status

from src.app.dependency_stubs import DatabaseHolderDep
from src.core.database import DatabaseHolder
from src.core.utils import cast_or_none

from .dtos import ComicBaseCreateDTO, ComicGetDTO
from .schemas import ComicCreateSchema, ComicGetSchema
from .services import ComicService
from .translations.dtos import TranslationCreateDTO
from .types import ComicID

router = APIRouter(
    tags=["Comics"],
)


@router.post("/comics", status_code=status.HTTP_201_CREATED)
async def create_comic(
    schema: ComicCreateSchema,
    holder: DatabaseHolder = Depends(DatabaseHolderDep),
) -> ComicGetSchema:
    comic_base = ComicBaseCreateDTO(
        issue_number=schema.issue_number,
        publication_date=schema.publication_date,
        xkcd_url=cast_or_none(str, schema.xkcd_url),
        explain_url=cast_or_none(str, schema.explain_url),
        reddit_url=cast_or_none(str, schema.reddit_url),
        link_on_click=cast_or_none(str, schema.link_on_click),
        is_interactive=schema.is_interactive,
        tags=schema.tags,
    )

    en_translation = TranslationCreateDTO(
        title=schema.en_translation.title,
        tooltip=schema.en_translation.tooltip,
        transcript=schema.en_translation.transcript,
        news_block=schema.en_translation.news_block,
        images=schema.en_translation.images,
    )

    comic_dto: ComicGetDTO = await ComicService(
        holder=holder,
    ).create_comic(
        comic_base=comic_base,
        en_translation=en_translation,
    )

    return ComicGetSchema.from_dto(comic_dto)


@router.get("/comics/get_by_id/{comic_id}")
async def get_comic_by_id(
    comic_id: ComicID,
    holder: DatabaseHolder = Depends(DatabaseHolderDep),
) -> ComicGetSchema:
    comic_dto = await ComicService(
        holder=holder,
    ).get_comic_by_id(comic_id)

    return ComicGetSchema.from_dto(comic_dto)
