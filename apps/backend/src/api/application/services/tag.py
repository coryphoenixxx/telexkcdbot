from api.application.dtos.common import TagName
from api.application.dtos.responses import TagResponseDTO
from api.core.value_objects import TagID
from api.infrastructure.database.repositories.tag import TagRepo
from api.infrastructure.database.transaction import TransactionManager


class TagService:
    def __init__(
        self,
        transaction: TransactionManager,
        repo: TagRepo,
    ) -> None:
        self._transaction = transaction
        self._repo = repo

    async def update(
        self,
        tag_id: TagID,
        name: TagName,
        blacklist_status: bool,
    ) -> TagResponseDTO:
        tag = await self._repo.update(
            tag_id=tag_id,
            name=name,
            blacklist_status=blacklist_status,
        )
        await self._transaction.commit()
        return tag

    async def delete(self, tag_id: TagID) -> None:
        await self._repo.delete(tag_id)
        await self._transaction.commit()
