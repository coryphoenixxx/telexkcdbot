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
            comic_repo, translation_repo = ComicRepo(self._uow.session), TranslationRepo(self._uow.session)

            comic_dto.issue_number = await self._generate_issue_number(comic_dto.issue_number, comic_repo)

            await comic_repo.create(comic_dto.comic)
            await translation_repo.add(comic_dto.translation)
            await ImageSaver(comic_dto.images).save()
            comic_model_with_tags_and_translation = \
                await comic_repo.get_by_issue_number(comic_dto.issue_number)

            await self._uow.commit()

            return ComicGetDTO.from_model(comic_model_with_tags_and_translation)

    async def get_comic_by_issue_number(self, issue_number: int) -> ComicGetDTO:
        async with self._uow:
            comic_repo = ComicRepo(self._uow.session)
            comic_model = await comic_repo.get_by_issue_number(issue_number)
            if comic_model:
                return ComicGetDTO.from_model(comic_model)

    @staticmethod
    async def _generate_issue_number(issue_number: int | None, comic_repo: ComicRepo):
        if not issue_number:
            issue_number = 30_000 + await comic_repo.get_extra_num()
        return issue_number
