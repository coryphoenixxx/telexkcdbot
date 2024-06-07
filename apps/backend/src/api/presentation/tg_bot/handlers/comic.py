from random import randint

from aiogram import Bot, F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InputMediaPhoto, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.utils.markdown import hbold, hlink
from dishka import FromDishka as Depends

from api.application.services import ComicService
from api.core.entities import IssueNumber
from api.presentation.tg_bot.config import BotConfig
from api.presentation.tg_bot.filters import ComicNumberFilter
from api.presentation.web.controllers.schemas import ComicResponseSchema

router = Router()

CURRENT_NUMBER = 0

COMIC_MESSAGE_ID = None


def build_navigation_keyboard():
    builder = InlineKeyboardBuilder()

    builder.add(InlineKeyboardButton(text="|<<", callback_data="nav_first"))
    builder.add(InlineKeyboardButton(text="<Prev", callback_data="nav_prev"))
    builder.add(InlineKeyboardButton(text="🎲Rand", callback_data="nav_random"))
    builder.add(InlineKeyboardButton(text="Next>", callback_data="nav_next"))
    builder.add(InlineKeyboardButton(text=">>|", callback_data="nav_last"))

    return builder.as_markup()


@router.message(ComicNumberFilter())
async def get_comic_by_number_handler(
        msg: Message,
        *,
        bot: Bot,
        config: Depends[BotConfig],
        service: Depends[ComicService],
):
    issue_number = IssueNumber(int(msg.text))

    dto = await service.get_by_issue_number(issue_number)

    comic = ComicResponseSchema.from_dto(dto=dto)

    caption = f"""{hbold(f"№{comic.number}")}. {hlink(comic.title, comic.xkcd_url)}"""
    image_url = config.webhook.url + "/static/" + comic.images[0].converted

    global COMIC_MESSAGE_ID

    new_msg = await msg.answer_photo(
        photo=image_url,
        caption=caption,
        show_caption_above_media=True,
        reply_markup=build_navigation_keyboard(),
    )

    COMIC_MESSAGE_ID = new_msg.message_id

    global CURRENT_NUMBER
    CURRENT_NUMBER = comic.number


@router.callback_query(F.data.startswith("nav_"))
async def navigation(
        callback: CallbackQuery,
        *,
        bot: Bot,
        config: Depends[BotConfig],
        service: Depends[ComicService],
):
    NEXT_NUMBER = None
    global CURRENT_NUMBER

    match callback.data:
        case "nav_first":
            NEXT_NUMBER = 1
        case "nav_prev":
            NEXT_NUMBER = CURRENT_NUMBER - 1
        case "nav_random":
            NEXT_NUMBER = randint(1, 1000)
        case "nav_next":
            NEXT_NUMBER = CURRENT_NUMBER + 1
        case "nav_last":
            NEXT_NUMBER = 1000

    dto = await service.get_by_issue_number(NEXT_NUMBER)

    comic = ComicResponseSchema.from_dto(dto=dto)

    caption = f"""{hbold(f"№{comic.number}")}. {hlink(comic.title, comic.xkcd_url)}"""
    image_url = config.webhook.url + "/static/" + comic.images[0].converted

    # await callback.message.edit_media(
    #     media=InputMediaPhoto(media=image_url, caption=caption, show_caption_above_media=True,),
    #     reply_markup=callback.message.reply_markup,
    # )

    global COMIC_MESSAGE_ID

    await bot.edit_message_media(
        chat_id=callback.message.chat.id,
        message_id=COMIC_MESSAGE_ID,
        media=InputMediaPhoto(
            media=image_url,
            caption=caption,
            show_caption_above_media=True,
        ),
        reply_markup=callback.message.reply_markup,
    )

    CURRENT_NUMBER = comic.number
