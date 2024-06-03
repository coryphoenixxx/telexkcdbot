import re

from aiogram import F, Router
from aiogram.filters import CommandObject, CommandStart
from aiogram.types import Message
from aiogram.utils.markdown import hbold, hcode, hlink
from aiogram.utils.media_group import MediaGroupBuilder
from bot.filters.main import ComicNumberFilter
from shared.api_rest_client import APIRESTClient

router = Router()

LANG = "RU"


@router.message(
    CommandStart(
        deep_link=True,
        magic=F.args.regexp(re.compile(r"user_(\d+)")),
    ),
)
async def start_handler(
    msg: Message,
    command: CommandObject,
) -> None:
    user_id = command.args.split("_")[1]

    await msg.answer(f"HELLO, {msg.chat.username} with {user_id=}")


@router.message(CommandStart())
async def start_handler(msg: Message) -> None:
    await msg.answer(f"HELLO, {msg.chat.username}. Base start.")


prepare_tag = lambda tag: "_".join(tag.split())

hspoiler = lambda text: f'<span class="tg-spoiler">{text}</span>'


def build_caption(
    number: int,
    en_title: str,
    xkcd_url: str,
    translation_title: str,
    translation_source_url: str,
    publication_date: str,
    tooltip: str,
    translation_tooltip: str,
    tags: list[str],
) -> str:
    # TODO: remove redundant slash in urls

    header = f"""{hbold(f"№{number}")}. {hlink(en_title, xkcd_url)}  |  {hspoiler(hlink(translation_title, translation_source_url))}\n"""
    publication_date = f"({hcode(publication_date)})"
    tooltip = f"{tooltip}\n{'-' * 20}\n{hspoiler(translation_tooltip)}"
    tags = "_" * 20 + "\n" + "".join([f"#{prepare_tag(t)}   " for t in tags])

    return "\n\n".join([header + publication_date, tooltip, tags]).strip()


@router.message(ComicNumberFilter())
async def get_comic_by_number_handler(
    msg: Message,
    api_client: APIRESTClient,
    img_prefix: str,
) -> None:
    comic = await api_client.get_comic_by_number(
        int(msg.text),
        languages=[LANG],
    )

    album_builder = MediaGroupBuilder()

    orig_img_url = img_prefix + comic["images"][0]["original"]
    tran_img_url = img_prefix + comic["translations"][LANG]["images"][0]["original"]

    print(tran_img_url)

    # album_builder.add_photo(media=orig_img_url)
    # album_builder.add_photo(media=tran_img_url, has_spoiler=True)

    caption = build_caption(
        number=comic["number"],
        en_title=comic["title"],
        translation_title=comic["translations"][LANG]["title"],
        publication_date=comic["publication_date"],
        tooltip=comic["tooltip"],
        translation_tooltip=comic["translations"][LANG]["tooltip"],
        xkcd_url=comic["xkcd_url"],
        translation_source_url=comic["translations"][LANG]["source_url"],
        tags=comic["tags"],
    )

    # album_builder.add_photo(media=orig_img_url, disable_content_type_detection=True)
    # album_builder.add_photo(
    #     media=tran_img_url,
    #     disable_content_type_detection=True,
    #     caption=caption,
    # )

    album_builder.add_document(media=orig_img_url, disable_content_type_detection=True)
    album_builder.add_document(
        media=tran_img_url,
        disable_content_type_detection=True,
        caption=caption,
    )

    if comic:
        await msg.answer_media_group(album_builder.build())
    else:
        await msg.reply("Comic no found")
