from sqlalchemy.exc import IntegrityError

from src.core.database import DatabaseHolder
from .dtos import ComicBaseCreateDTO, ComicGetDTO
from .exceptions import ComicNotFoundError, ComicIssueNumberUniqueError
from .translations.dtos import TranslationCreateDTO
from .translations.exceptions import TranslationTitleUniqueError
from .types import ComicID


class ComicService:
    def __init__(self, holder: DatabaseHolder):
        self._holder = holder

    async def create_comic(
        self,
        comic_base: ComicBaseCreateDTO,
        en_translation: TranslationCreateDTO,
    ) -> ComicGetDTO:
        async with self._holder:
            try:
                comic_id = await self._holder.comic_repo.create(comic_base)

                en_translation.comic_id = comic_id
                await self._holder.translation_repo.create(en_translation)

                await self._holder.commit()
            except IntegrityError as err:
                constraint = err.__cause__.__cause__.constraint_name
                if constraint == "ix_unique_issue_number_if_not_none":
                    raise ComicIssueNumberUniqueError(
                        issue_number=comic_base.issue_number
                    )
                elif constraint == "ix_unique_translation_title_not_draft":
                    raise TranslationTitleUniqueError(
                        title=en_translation.title, language=en_translation.language
                    )
            else:
                comic_model = await self._holder.comic_repo.get_by_id(comic_id)
                return ComicGetDTO.from_model(comic_model)

    async def get_comic_by_id(self, comic_id: ComicID) -> ComicGetDTO:
        async with self._holder:
            comic_model = await self._holder.comic_repo.get_by_id(comic_id)

            if not comic_model:
                raise ComicNotFoundError(comic_id=comic_id)

            return ComicGetDTO.from_model(comic_model)
