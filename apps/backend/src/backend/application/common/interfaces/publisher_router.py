from functools import singledispatchmethod
from typing import Any, NoReturn, Protocol

from pydantic import BaseModel

from backend.application.common.interfaces.file_storages import TempFileID
from backend.core.value_objects import TranslationImageID


class ProcessTranslationImageMessage(BaseModel):
    temp_image_id: TempFileID
    translation_image_id: TranslationImageID


class NewComicMessage(BaseModel):
    comic_id: int


class PublisherRouterInterface(Protocol):
    @singledispatchmethod
    async def publish(self, msg: Any, **kwargs: Any) -> NoReturn:
        raise NotImplementedError

    @publish.register  # type: ignore[arg-type]
    async def _(self, msg: ProcessTranslationImageMessage, **kwargs: Any) -> None: ...

    @publish.register  # type: ignore[arg-type]
    async def _(self, msg: NewComicMessage, **kwargs: Any) -> None: ...
