import re

from aiogram import F, Router
from aiogram.filters import CommandObject, CommandStart
from aiogram.types import Message

router = Router()


@router.message(
    CommandStart(
        deep_link=True,
        magic=F.args.regexp(re.compile(r"user_(\d+)")),
    ),
)
async def start_handler_with_user_id(
    msg: Message,
    command: CommandObject,
) -> None:
    user_id = command.args.split("_")[1]

    await msg.answer(f"HELLO, {msg.chat.username} with {user_id=}")


@router.message(CommandStart())
async def start_handler(msg: Message) -> None:
    await msg.answer(f"HELLO, {msg.chat.username}. Base start.")
