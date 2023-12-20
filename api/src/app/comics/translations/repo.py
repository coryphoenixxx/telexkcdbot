from sqlalchemy import false, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from .dtos import TranslationCreateDTO
from .models import TranslationModel


class TranslationRepo:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def add(
        self,
        translation_dto: TranslationCreateDTO,
        skip_check_for_drafts: bool = False,
    ) -> TranslationModel:
        if translation_dto.is_draft is False and skip_check_for_drafts is False:
            await self._check_non_draft_already_exist(translation_dto)

        stmt = (
            insert(TranslationModel).values(translation_dto.to_dict()).returning(TranslationModel)
        )
        result = (await self._session.scalars(stmt)).one()
        return result

    async def _check_non_draft_already_exist(self, translation_dto: TranslationCreateDTO):
        stmt = (
            select(func.count("*"))
            .select_from(TranslationModel)
            .where(
                TranslationModel.is_draft == false(),
                TranslationModel.issue_number == translation_dto.issue_number,
                TranslationModel.language == translation_dto.language,
            )
        )
        non_draft_num = await self._session.scalar(stmt)
        if non_draft_num:
            raise ValueError("Non-draft translation for this comic already exists.")
