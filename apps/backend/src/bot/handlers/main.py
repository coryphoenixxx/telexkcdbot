import re

from aiogram import Router, F
from aiogram.filters import CommandObject, CommandStart
from aiogram.types import Message

from bot.filters.main import ComicNumberFilter
from shared.api_rest_client import APIRESTClient

router = Router()


@router.message(
    CommandStart(
        deep_link=True,
        magic=F.args.regexp(re.compile(r"user_(\d+)")),
    )
)
async def start_handler(
    msg: Message,
    command: CommandObject,
) -> None:
    user_id = command.args.split("_")[1]

    await msg.answer(f"HELLO, {msg.chat.username} with {user_id=}")


@router.message(CommandStart())
async def start_handler(
    msg: Message
) -> None:
    await msg.answer(f"HELLO, {msg.chat.username}. Base start.")


@router.message(ComicNumberFilter())
async def get_comic_by_number_handler(msg: Message, api_client: APIRESTClient) -> None:
    comic = await api_client.get_comic_by_number(int(msg.text))

    if comic:
        await msg.reply(comic["translations"][0]["title"])
    else:
        await msg.reply("Comic no found")
