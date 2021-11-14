import asyncio
import csv

from tqdm import trange, tqdm

from src.bot.loader import comics_db, parser
from src.bot.logger import logger
from src.bot.paths import PATH_TO_RU_COMICS_DATA


buffer = []
sem = asyncio.Semaphore(64)  # Limits simultaneous connections on Windows
ru_comics_data = {}


def preprocess_path(comic_id: str) -> str:
    filename = list((PATH_TO_RU_COMICS_DATA / 'images').glob(f'{comic_id}.*'))[0].name
    return 'static/ru_comics_data/images/' + filename


def retrieve_from_csv_to_dict():
    with open(PATH_TO_RU_COMICS_DATA / 'data.csv', 'r', encoding='utf-8') as csv_file:
        csv_reader = csv.DictReader(csv_file, delimiter=',')
        for row in tqdm(list(csv_reader)):
            ru_comics_data[row['comic_id']] = {
                'ru_title': row['ru_title'],
                'ru_img_url': preprocess_path(row['comic_id']),
                'ru_comment': row['ru_comment']
            }


async def get_ru_comic_data_by_id(comic_id: int) -> dict:
    keys = ('ru_title', 'ru_img_url', 'ru_comment')

    if not ru_comics_data.get(str(comic_id)):
        return dict(zip(keys, ('',) * 3))
    else:
        return ru_comics_data[str(comic_id)]


async def get_full_comic_data(comic_id: int) -> tuple:
    full_comic_data = await parser.get_en_comic_data_by_id(comic_id)
    full_comic_data.update(await get_ru_comic_data_by_id(comic_id))
    return tuple(full_comic_data.values())


async def put_comics_data_to_buffer(comic_id):
    async with sem:
        comic_data = await get_full_comic_data(comic_id)
    buffer.append(comic_data)


async def write_to_db():
    buffer.sort(key=lambda x: x[0])
    while buffer:
        await comics_db.add_new_comic(buffer.pop(0))


async def gather(start, end, all_comics_ids):
    tasks = []
    for comic_id in range(start, end):
        if comic_id not in all_comics_ids:
            task = asyncio.create_task(put_comics_data_to_buffer(comic_id))
            tasks.append(task)

    await asyncio.gather(*tasks)


async def initial_filling_of_comics_db():
    logger.info("Retrieving ru comics data from csv started...")
    retrieve_from_csv_to_dict()
    logger.info("Retrieving ru comics data from csv finished!")

    logger.info("Filling the comics db started...")
    all_comics_ids = await comics_db.get_all_comics_ids()
    latest = await parser.get_xkcd_latest_comic_id()
    chunk = 20

    for i in trange(1, latest + 1, chunk):
        end = i + chunk
        if end > latest:
            end = latest + 1

        await gather(i, end, all_comics_ids)
        await write_to_db()
    logger.info("Filling the comics db finished!")

    global ru_comics_data
    del ru_comics_data
