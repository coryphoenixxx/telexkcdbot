from dataclasses import dataclass

from backend.application.comic.dtos import TagResponseDTO, TagUpdateDTO
from backend.application.comic.interfaces import TagRepoInterface
from backend.application.common.interfaces import TransactionManagerInterface
from backend.application.utils import slugify
from backend.core.value_objects import TagID


@dataclass(slots=True)
class TagService:
    transaction: TransactionManagerInterface
    repo: TagRepoInterface

    async def update(
        self,
        tag_id: TagID,
        dto: TagUpdateDTO,
    ) -> TagResponseDTO:
        data = {**dto}
        if data.get("name"):
            name = dto["name"].value
            data["name"], data["slug"] = name, slugify(name)

        resp_dto = await self.repo.update(tag_id, data)
        await self.transaction.commit()
        return resp_dto

    async def delete(self, tag_id: TagID) -> None:
        await self.repo.delete(tag_id)
        await self.transaction.commit()
