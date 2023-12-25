from src.core.utils.uow import UOW

from .dtos import ComicGetDTO, ComicTotalDTO
from .image_utils.saver import ImageSaver
from .repo import ComicRepo
from .translations.repo import TranslationRepo


class ComicsService:
    def __init__(self, uow: UOW):
        self._uow = uow

    async def create_comic(
        self,
        comic_dto: ComicTotalDTO,
    ) -> ComicGetDTO:
        async with (self._uow):
            comic_repo, translation_repo = ComicRepo(self._uow.session), TranslationRepo(
                self._uow.session,
            )

            comic_id = await comic_repo.create(comic_dto.comic)
            await translation_repo.add_to_comic(comic_id, comic_dto.translation)
            await self._uow.commit()

            comic_model = await comic_repo.get_by_id(comic_id)

            await ImageSaver(comic_dto.images).save()

            return ComicGetDTO.from_model(comic_model)

    async def get_comic_by_issue_number(self, issue_number: int) -> ComicGetDTO:
        comic_model = await ComicRepo(self._uow.session).get_by_issue_number(issue_number)
        if comic_model:
            return ComicGetDTO.from_model(comic_model)

    async def get_comic_by_id(self, issue_number: int) -> ComicGetDTO:
        comic_model = await ComicRepo(self._uow.session).get_by_issue_number(issue_number)
        if comic_model:
            return ComicGetDTO.from_model(comic_model)
