import asyncio

import aioschedule

from bot.api_client import api
from bot.comic_data_getter import comics_data_getter
from bot.common_utils import broadcast
from bot.models import TotalComicData


async def get_and_broadcast_new_comic() -> None:
    db_last_comic_id = await api.get_latest_comic_id()
    real_last_comic_id = await comics_data_getter.get_xkcd_latest_comic_id()

    if real_last_comic_id > db_last_comic_id:
        for comic_id in range(db_last_comic_id + 1, real_last_comic_id + 1):
            xkcd_comic_data = await comics_data_getter.get_xkcd_comic_data_by_id(comic_id)

            await api.add_new_comic(
                TotalComicData(
                    comic_id=xkcd_comic_data.comic_id,
                    title=xkcd_comic_data.title,
                    img_url=xkcd_comic_data.img_url,
                    comment=xkcd_comic_data.comment,
                    public_date=xkcd_comic_data.public_date,
                )
            )
        await broadcast(comic_id=real_last_comic_id)


async def checker() -> None:
    await get_and_broadcast_new_comic()
    aioschedule.every(15).minutes.do(get_and_broadcast_new_comic)
    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(300)
