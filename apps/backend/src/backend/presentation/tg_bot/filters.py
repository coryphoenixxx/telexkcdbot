from aiogram.filters import BaseFilter
from aiogram.types import Message


class ComicNumberFilter(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        return message.text.isdigit()
