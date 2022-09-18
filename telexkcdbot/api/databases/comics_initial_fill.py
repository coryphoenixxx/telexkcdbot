import asyncio
import sys
from typing import Sequence

from loguru import logger
from tqdm import tqdm

from telexkcdbot.api.databases.database import db
from telexkcdbot.bot.comic_data_getter import comics_data_getter
from telexkcdbot.bot.common_utils import cut_into_chunks

chunk_size = 20
buffer = []
sem = asyncio.Semaphore(64)  # Limits simultaneous connections on Windows


async def get_and_put_comic_data_to_buffer(comic_id: int) -> None:
    async with sem:
        comic_data = await comics_data_getter.get_total_comic_data(comic_id)
    buffer.append(comic_data)


async def get_comics_data(chunk: list[int], all_comics_ids: Sequence[int]) -> None:
    tasks = []
    for comic_id in chunk:
        if comic_id not in all_comics_ids:
            task = asyncio.create_task(get_and_put_comic_data_to_buffer(comic_id))
            tasks.append(task)
    await asyncio.gather(*tasks)


async def write_to_db() -> None:
    buffer.sort(key=lambda x: int(x.comic_id))
    while buffer:
        await db.comics.add_new_comic(buffer.pop(0))


async def comics_initial_fill() -> None:
    logger.info("Retrieving ru comics data from csv started...")
    comics_data_getter.retrieve_from_csv_to_dict()

    logger.info("Filling the comics db started...")
    all_comics_ids = await db.comics.get_all_comics_ids()
    latest = await comics_data_getter.get_xkcd_latest_comic_id()

    pbar = tqdm(total=latest, file=sys.stdout)
    for chunk in cut_into_chunks(list(range(1, latest + 1)), chunk_size):
        await get_comics_data(chunk, all_comics_ids)
        await write_to_db()
        pbar.update(len(chunk))

    logger.info("Finished!")
    comics_data_getter.clean()
