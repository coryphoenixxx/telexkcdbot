from aiogram.filters import BaseFilter
from aiogram.types import Message


class ComicNumberFilter(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        if message.text.isdigit():
            return True
        return False
