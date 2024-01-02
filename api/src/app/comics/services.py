from src.core.database.uow import UOW

from .dtos import ComicCreateTotalDTO, ComicGetDTO
from .repo import ComicRepo
from .translations.repo import TranslationRepo


class ComicsService:
    def __init__(self, uow: UOW):
        self._uow = uow

    async def create_comic(
            self,
            comic_dto: ComicCreateTotalDTO,
    ) -> ComicGetDTO:
        async with self._uow:  # type: UOW
            comic_repo = ComicRepo(self._uow.session)
            translation_repo = TranslationRepo(self._uow.session)

            comic_id = await comic_repo.create(comic_dto.comic)
            await translation_repo.add_to_comic(comic_id, comic_dto.en_translation)
            await self._uow.commit()

            comic_model = await comic_repo.get_by_id(comic_id)

        return ComicGetDTO.from_model(comic_model)

    async def get_comic_by_id(self, comic_id: int) -> ComicGetDTO:
        comic_model = await ComicRepo(self._uow.session).get_by_id(comic_id)
        if comic_model:
            return ComicGetDTO.from_model(comic_model)
