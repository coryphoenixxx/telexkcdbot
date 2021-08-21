from tqdm import trange

from bot.loader import *


comics_data = []
sem = asyncio.Semaphore(64)  # Limits simultaneous connections on Windows


async def get_comics_data(comic_id):
    async with sem:
        comic_data = await parser.get_full_comic_data(comic_id)
    comics_data.append(comic_data)


async def write_to_db():
    comics_data.sort(key=lambda x: x[0])

    while comics_data:
        await comics_db.add_new_comic(comics_data.pop(0))


async def gather(start, end, all_comics_ids):
    tasks = []

    for comic_id in range(start, end):
        if comic_id not in all_comics_ids:
            task = asyncio.create_task(get_comics_data(comic_id))
            tasks.append(task)

    await asyncio.gather(*tasks)


async def main():
    logger.info("Start filling the comics db.")

    all_comics_ids = await comics_db.get_all_comics_ids()
    latest = await parser.get_xkcd_latest_comic_id()
    chunk = 20

    for i in trange(1, latest + 1, chunk):
        end = i + chunk
        if end > latest:
            end = latest + 1

        await gather(i, end, all_comics_ids)
        await write_to_db()

    logger.info("Finish filling the comics db.")


async def fill_comics_db():
    await main()
