from random import randint

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    InputMediaPhoto,
    Message,
)
from aiogram.utils.markdown import hbold, hlink
from dishka import FromDishka as Depends

from api.application.services import ComicService
from api.core.configs.bot import BotConfig
from api.core.value_objects import IssueNumber
from api.presentation.tg_bot.filters import ComicNumberFilter
from api.presentation.tg_bot.keyboards.navigation import build_navigation_keyboard
from api.presentation.web.controllers.schemas import (
    ComicResponseSchema,
    TranslationImageResponseSchema,
)

router = Router()


class ImageStorage:
    def __init__(self) -> None:
        self._storage = {}

    def get_image(self, image_url: str) -> str:
        image_file_id = self._storage.get(self._cut(image_url))

        return image_file_id or image_url

    def set_image(self, image_url: str, image_file_id: str) -> None:
        self._storage[self._cut(image_url)] = image_file_id

    @staticmethod
    def _cut(image_url: str) -> str:
        return image_url.rsplit("/", maxsplit=1)[1]


def build_caption(comic: ComicResponseSchema) -> str:
    return f"""{hbold(f"№{comic.number}")}. {hlink(comic.title, comic.xkcd_url)}\n"""


def build_image_url(
    webhook_url: str,
    comic_images: list[TranslationImageResponseSchema],
) -> str:
    return webhook_url + "/static/" + comic_images[0].converted


def calc_next_number(
    data: str,
    cur_pos: IssueNumber,
    latest: IssueNumber,
) -> IssueNumber:
    match data:
        case "nav_first":
            next_number = 1
        case "nav_prev":
            next_number = cur_pos - 1
            if next_number <= 0:
                next_number = latest
        case "nav_random":
            next_number = randint(1, latest)  # noqa: S311
        case "nav_next":
            next_number = cur_pos + 1
            if next_number > latest:
                next_number = 1
        case "nav_last":
            next_number = latest
        case _:
            raise

    return next_number


image_storage = ImageStorage()


@router.message(ComicNumberFilter())
async def get_comic_by_number_handler(
    msg: Message,
    *,
    config: Depends[BotConfig],
    service: Depends[ComicService],
    state: FSMContext,
) -> None:
    issue_number = IssueNumber(int(msg.text))

    dto = await service.get_by_issue_number(issue_number)

    comic = ComicResponseSchema.from_dto(dto=dto)

    image_url = build_image_url(webhook_url=config.webhook.url, comic_images=comic.image)

    answer = await msg.answer_photo(
        photo=image_storage.get_image(image_url),
        caption=build_caption(comic),
        show_caption_above_media=True,
        reply_markup=build_navigation_keyboard(),
    )

    image_storage.set_image(image_url=image_url, image_file_id=answer.photo[-1].file_id)

    await state.update_data(position=issue_number)


@router.callback_query(F.data.startswith("nav_"))
async def navigation(
    callback: CallbackQuery,
    *,
    config: Depends[BotConfig],
    service: Depends[ComicService],
    state: FSMContext,
) -> None:
    next_number = calc_next_number(
        data=callback.data,
        cur_pos=(await state.get_data())["position"],
        latest=await service.get_latest_issue_number(),
    )

    comic = ComicResponseSchema.from_dto(dto=await service.get_by_issue_number(next_number))

    image_url = build_image_url(webhook_url=config.webhook.url, comic_images=comic.image)

    answer = await callback.message.edit_media(
        media=InputMediaPhoto(
            media=image_storage.get_image(image_url),
            caption=build_caption(comic),
            show_caption_above_media=True,
        ),
        reply_markup=callback.message.reply_markup,
    )

    image_storage.set_image(image_url=image_url, image_file_id=answer.photo[-1].file_id)

    await state.update_data(position=next_number)
