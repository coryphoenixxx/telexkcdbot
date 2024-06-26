from collections.abc import Sequence
from typing import TypeVar

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.interfaces import ORMOption

from api.infrastructure.database.models import BaseModel

Model = TypeVar("Model", bound=BaseModel)


class BaseRepo:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def _get_model_by_id(
        self,
        model: type[Model],
        id_: int,
        *,
        options: Sequence[ORMOption] | None = None,
    ) -> Model:
        return await self._session.get(model, id_, options=options)
