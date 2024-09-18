from dataclasses import dataclass

from backend.application.comic.dtos import TagResponseDTO, TagUpdateDTO
from backend.application.comic.interfaces import TagRepoInterface
from backend.application.common.interfaces import TransactionManagerInterface
from backend.application.utils import slugify
from backend.core.value_objects import TagID


@dataclass(slots=True)
class UpdateTagInteractor:
    tag_repo: TagRepoInterface
    transaction: TransactionManagerInterface

    async def execute(
        self,
        tag_id: TagID,
        dto: TagUpdateDTO,
    ) -> TagResponseDTO:
        data = {**dto}
        if data.get("name"):
            name = dto["name"].value
            data["name"], data["slug"] = name, slugify(name)

        resp_dto = await self.tag_repo.update(tag_id, data)
        await self.transaction.commit()
        return resp_dto


@dataclass(slots=True)
class DeleteTagInteractor:
    tag_repo: TagRepoInterface
    transaction: TransactionManagerInterface

    async def execute(self, tag_id: TagID) -> None:
        await self.tag_repo.delete(tag_id)
        await self.transaction.commit()
